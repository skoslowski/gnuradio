# Copyright 2008-2016 Free Software Foundation, Inc.
# This file is part of GNU Radio
#
# GNU Radio Companion is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# GNU Radio Companion is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

from __future__ import absolute_import, print_function

import glob
import os
import logging

import six
from six.moves import range
import yaml

from . import (
    ParseXML, Messages, Constants,
    blocks, utils, schema_checker
)

from .Config import Config
from .Element import Element
from .generator import Generator
from .FlowGraph import FlowGraph
from .Connection import Connection
from .Port import Port, PortClone
from .Param import Param

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Platform(Element):

    is_platform = True

    def __init__(self, *args, **kwargs):
        """ Make a platform for GNU Radio """
        Element.__init__(self, parent=None)

        self.config = self.Config(*args, **kwargs)
        self.block_docstrings = {}
        self.block_docstrings_loaded_callback = lambda: None  # dummy to be replaced by BlockTreeWindow

        self._docstring_extractor = utils.extract_docs.SubprocessLoader(
            callback_query_result=self._save_docstring_extraction_result,
            callback_finished=lambda: self.block_docstrings_loaded_callback()
        )

        self.blocks = {}
        self._blocks_n = {}
        self._block_categories = {}
        self.domains = {}
        self.connection_templates = {}

        self._auto_hier_block_generate_chain = set()

        # Create a dummy flow graph for the blocks
        self._flow_graph = Element.__new__(FlowGraph)
        Element.__init__(self._flow_graph, self)
        self._flow_graph.connections = []

        if not yaml.__with_libyaml__:
            print("Warning: slow block loading")
        self.build_block_library()

    def __str__(self):
        return 'Platform - {}'.format(self.config.name)

    @staticmethod
    def find_file_in_paths(filename, paths, cwd):
        """Checks the provided paths relative to cwd for a certain filename"""
        if not os.path.isdir(cwd):
            cwd = os.path.dirname(cwd)
        if isinstance(paths, str):
            paths = (p for p in paths.split(':') if p)

        for path in paths:
            path = os.path.expanduser(path)
            if not os.path.isabs(path):
                path = os.path.normpath(os.path.join(cwd, path))
            file_path = os.path.join(path, filename)
            if os.path.exists(os.path.normpath(file_path)):
                return file_path

    def load_and_generate_flow_graph(self, file_path, out_path=None, hier_only=False):
        """Loads a flow graph from file and generates it"""
        Messages.set_indent(len(self._auto_hier_block_generate_chain))
        Messages.send('>>> Loading: {}\n'.format(file_path))
        if file_path in self._auto_hier_block_generate_chain:
            Messages.send('    >>> Warning: cyclic hier_block dependency\n')
            return None, None
        self._auto_hier_block_generate_chain.add(file_path)
        try:
            flow_graph = self.get_new_flow_graph()
            flow_graph.grc_file_path = file_path
            # Other, nested hier_blocks might be auto-loaded here
            flow_graph.import_data(self.parse_flow_graph(file_path))
            flow_graph.rewrite()
            flow_graph.validate()
            if not flow_graph.is_valid():
                raise Exception('Flowgraph invalid')
            if hier_only and not flow_graph.get_option('generate_options').startswith('hb'):
                raise Exception('Not a hier block')
        except Exception as e:
            Messages.send('>>> Load Error: {}: {}\n'.format(file_path, str(e)))
            return None, None
        finally:
            self._auto_hier_block_generate_chain.discard(file_path)
            Messages.set_indent(len(self._auto_hier_block_generate_chain))

        try:
            generator = self.Generator(flow_graph, out_path or file_path)
            Messages.send('>>> Generating: {}\n'.format(generator.file_path))
            generator.write()
        except Exception as e:
            Messages.send('>>> Generate Error: {}: {}\n'.format(file_path, str(e)))
            return None, None

        if flow_graph.get_option('generate_options').startswith('hb'):
            # self.load_block_xml(generator.file_path_xml)
            # TODO: implement yml output for hier blocks
            pass
        return flow_graph, generator.file_path

    def build_block_library(self):
        """load the blocks and block tree from the search paths"""
        self._docstring_extractor.start()

        # Reset
        self.blocks.clear()
        self._blocks_n.clear()
        self._block_categories.clear()
        self.domains.clear()
        self.connection_templates.clear()

        # FIXME: remove this as soon as converter is stable
        from ..converter import Converter
        converter = Converter(self.config.block_paths, self.config.yml_block_cache)
        converter.run()
        logging.info('XML converter done.')

        for file_path in self.iter_files_in_block_path():
            try:
                data = converter.cache[file_path]
            except KeyError:
                with open(file_path) as fp:
                    data = yaml.load(fp)

            if file_path.endswith('.block.yml'):
                loader = self.load_block_description
                scheme = schema_checker.BLOCK_SCHEME
            elif file_path.endswith('.domain.yml'):
                loader = self.load_domain_description
                scheme = schema_checker.DOMAIN_SCHEME
            elif file_path.endswith('.tree.yml'):
                loader = self.load_category_tree_description
                scheme = None
            else:
                continue

            try:
                checker = schema_checker.Validator(scheme)
                passed = checker.run(data)
                for msg in checker.messages:
                    logger.warning('{:<40s} {}'.format(os.path.basename(file_path), msg))
                if not passed:
                    logger.info('YAML schema check failed for: ' + file_path)

                loader(data, file_path)
            except Exception as error:
                logger.exception('Error while loading %s', file_path)
                logger.exception(error)
                raise

        # Add blocks to block tree
        for key, block in six.iteritems(self.blocks):
            category = self._block_categories.get(key, block.category)
            # Blocks with empty categories are hidden
            if not category:
                continue
            root = category[0]
            if root.startswith('[') and root.endswith(']'):
                category[0] = root[1:-1]
            else:
                category.insert(0, Constants.DEFAULT_BLOCK_MODULE_NAME)
            block.category = category

        self._docstring_extractor.finish()
        # self._docstring_extractor.wait()

    def iter_files_in_block_path(self, ext='yml'):
        """Iterator for block descriptions and category trees"""
        for block_path in self.config.block_paths:
            if os.path.isfile(block_path):
                yield block_path
            elif os.path.isdir(block_path):
                pattern = os.path.join(block_path, '**.' + ext)
                yield_from = glob.iglob(pattern)
                for file_path in yield_from:
                    yield file_path

    def _save_docstring_extraction_result(self, key, docstrings):
        docs = {}
        for match, docstring in six.iteritems(docstrings):
            if not docstring or match.endswith('_sptr'):
                continue
            docstring = docstring.replace('\n\n', '\n').strip()
            docs[match] = docstring
        self.block_docstrings[key] = docs

    ##############################################
    # YAML
    ##############################################

    def load_block_description(self, data, file_path):
        block_id = data.pop('id').rstrip('_')

        if block_id in self.blocks:
            logger.warning('Block with id "%s" overwritten by %s', block_id, file_path)

        # Store the block
        self.blocks[block_id] = self.get_new_block(self._flow_graph, block_id, **data)
        self._blocks_n[block_id] = data

        templates = data.get('templates', {})
        self._docstring_extractor.query(
            block_id, templates.get('imports', ''), templates.get('make', ''),
        )

    def load_domain_description(self, data, file_path):
        log = logger.getChild('domain_loader')
        domain_id = data['id']
        if domain_id in self.domains:  # test against repeated keys
            log.debug('Domain "{}" already exists. Ignoring: %s', file_path)
            return

        color = data.get('color', '')
        if color.startswith('#'):
            try:
                tuple(int(color[o:o + 2], 16) / 255.0 for o in range(1, 6, 2))
            except ValueError:
                log.warning('Cannot parse color code "%s" in %s', color, file_path)
                return

        self.domains[domain_id] = dict(
            name=data.get('label', domain_id),
            multiple_sinks=data.get('multiple_connections_per_input', True),
            multiple_sources=data.get('multiple_connections_per_output', False),
            color=color
        )
        for connection in data.get('templates', []):
            try:
                source_id, sink_id = connection.get('type', [])
            except ValueError:
                continue
            connection_id = str(source_id), str(sink_id)
            self.connection_templates[connection_id] = connection.get('make', '')

    def load_category_tree_description(self, data, file_path):
        """Parse category tree file and add it to list"""
        log = logger.getChild('tree_loader')
        log.debug('Loading %s', file_path)
        path = []

        def load_category(name, elements):
            if not isinstance(name, str):
                log.debug('invalid name %r', name)
                return
            if isinstance(elements, list):
                pass
            elif isinstance(elements, str):
                elements = [elements]
            else:
                log.debug('Ignoring elements of %s', name)
                return
            path.append(name)
            for element in elements:
                if isinstance(element, str):
                    block_id = element
                    self._block_categories[block_id] = list(path)
                elif isinstance(element, dict):
                    load_category(*next(six.iteritems(element)))
                else:
                    log.debug('Ignoring some elements of %s', name)
            path.pop()

        try:
            module_name, categories = next(six.iteritems(data))
        except (AttributeError, StopIteration):
            log.warning('no valid data found')
        else:
            load_category(module_name, categories)

    ##############################################
    # Access
    ##############################################

    def parse_flow_graph(self, flow_graph_file):
        """
        Parse a saved flow graph file.
        Ensure that the file exists, and passes the dtd check.

        Args:
            flow_graph_file: the flow graph file

        Returns:
            nested data
        @throws exception if the validation fails
        """
        flow_graph_file = flow_graph_file or self.config.default_flow_graph
        open(flow_graph_file, 'r').close()  # Test open
        ParseXML.validate_dtd(flow_graph_file, Constants.FLOW_GRAPH_DTD)
        return ParseXML.from_file(flow_graph_file)

    def get_blocks(self):
        return list(self.blocks.values())

    def get_generate_options(self):
        gen_opts = self.blocks['options'].params['generate_options']
        generate_mode_default = gen_opts.get_value()
        return [(value, name, value == generate_mode_default)
                for value, name in gen_opts.options.items()]

    ##############################################
    # Factories
    ##############################################
    Config = Config
    Generator = Generator
    FlowGraph = FlowGraph
    Connection = Connection

    block_classes = {
        None: blocks.Block,  # default
        'epy_block': blocks.EPyBlock,
        '_dummy': blocks.DummyBlock,
    }
    port_classes = {
        None: Port,  # default
        'clone': PortClone,  # default
    }
    param_classes = {
        None: Param,  # default
    }

    def get_new_flow_graph(self):
        return self.FlowGraph(parent=self)

    def get_new_block(self, parent, block_id, **kwargs):
        cls = self.block_classes.get(block_id, self.block_classes[None])
        if not kwargs:
            kwargs = self._blocks_n[block_id]
        return cls(parent, id=block_id, **kwargs)

    def get_new_param(self, parent, **kwargs):
        cls = self.param_classes[kwargs.pop('cls_key', None)]
        return cls(parent, **kwargs)

    def get_new_port(self, parent, **kwargs):
        cls = self.port_classes[kwargs.pop('cls_key', None)]
        return cls(parent, **kwargs)
