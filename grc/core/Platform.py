"""
Copyright 2008-2016 Free Software Foundation, Inc.
This file is part of GNU Radio

GNU Radio Companion is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

GNU Radio Companion is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

from __future__ import absolute_import, print_function

import glob
import os
import sys

import six
from six.moves import range
import yaml

from . import ParseXML, Messages, Constants, legacy

from .Config import Config
from .Element import Element
from .generator import Generator
from .FlowGraph import FlowGraph
from .Connection import Connection
from . import Block, utils
from .Port import Port, PortClone
from .Param import Param


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

    def load_and_generate_flow_graph(self, file_path):
        """Loads a flow graph from file and generates it"""
        Messages.set_indent(len(self._auto_hier_block_generate_chain))
        Messages.send('>>> Loading: %r\n' % file_path)
        if file_path in self._auto_hier_block_generate_chain:
            Messages.send('    >>> Warning: cyclic hier_block dependency\n')
            return False
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
            if not flow_graph.get_option('generate_options').startswith('hb'):
                raise Exception('Not a hier block')
        except Exception as e:
            Messages.send('>>> Load Error: {}: {}\n'.format(file_path, str(e)))
            return False
        finally:
            self._auto_hier_block_generate_chain.discard(file_path)
            Messages.set_indent(len(self._auto_hier_block_generate_chain))

        try:
            Messages.send('>>> Generating: {}\n'.format(file_path))
            generator = self.Generator(flow_graph, file_path)
            generator.write()
        except Exception as e:
            Messages.send('>>> Generate Error: {}: {}\n'.format(file_path, str(e)))
            return False

        self.load_block_xml(generator.file_path_xml)
        return True

    def build_block_library(self):
        """load the blocks and block tree from the search paths"""
        self._docstring_extractor.start()

        # Reset
        self.blocks.clear()
        self._blocks_n.clear()
        self._block_categories.clear()
        self.domains.clear()
        self.connection_templates.clear()
        ParseXML.xml_failures.clear()

        # Try to parse and load blocks
        for xml_file in self.iter_files_in_block_path(ext='xml'):
            try:
                if xml_file.endswith("block_tree.xml"):
                    self.load_category_tree_xml(xml_file)
                elif xml_file.endswith('domain.xml'):
                    self.load_domain_xml(xml_file)
                else:
                    self.load_block_xml(xml_file)
            except ParseXML.XMLSyntaxError as e:
                # print >> sys.stderr, 'Warning: Block validation failed:\n\t%s\n\tIgnoring: %s' % (e, xml_file)
                pass
            except Exception as e:
                raise

        for file_path in self.iter_files_in_block_path():
            with open(file_path) as fp:
                data = yaml.load(fp)
            try:
                if file_path.endswith('.block.yml'):
                    self.load_block_description(data, file_path)
            except Exception as e:
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

    def load_block_xml(self, xml_file):
        """Load block description from xml file"""
        if 'qtgui_' in xml_file or '.grc_gnuradio/' in xml_file:
            return

        key_from_xml = os.path.basename(xml_file)[:-4]
        yml_file = os.path.join(self.config.yml_block_cache,
                                key_from_xml + '.block.yml')

        if os.path.exists(yml_file):
            xml_time = os.stat(xml_file).st_mtime
            yml_time = os.stat(yml_file).st_mtime
            converter_time = os.stat(
                legacy.block_xml_converter.__file__.rstrip('c')
            ).st_mtime
            if yml_time > xml_time and yml_time > converter_time:
                return  # yml file up-to-date

        # print('Converting', xml_file)
        key, data = legacy.convert_xml(xml_file)

        # if key_from_xml != key:
        #     print('Warning: key is not filename in', xml_file)

        with open(yml_file, 'w') as yml_file:
            yml_file.write(data)

    def load_category_tree_xml(self, xml_file):
        """Validate and parse category tree file and add it to list"""
        ParseXML.validate_dtd(xml_file, Constants.BLOCK_TREE_DTD)
        xml = ParseXML.from_file(xml_file)
        path = []

        def load_category(cat_n):
            path.append(cat_n.get('name').strip())
            for block_key in cat_n.get('block', []):
                if block_key not in self._block_categories:
                    self._block_categories[block_key] = list(path)
            for sub_cat_n in cat_n.get('cat', []):
                load_category(sub_cat_n)
            path.pop()

        load_category(xml.get('cat', {}))

    def load_domain_xml(self, xml_file):
        """Load a domain properties and connection templates from XML"""
        ParseXML.validate_dtd(xml_file, Constants.DOMAIN_DTD)
        n = ParseXML.from_file(xml_file).get('domain')

        key = n.get('key')
        if not key:
            print('Warning: Domain with emtpy key.\n\tIgnoring: {}'.format(xml_file), file=sys.stderr)
            return
        if key in self.domains:  # test against repeated keys
            print('Warning: Domain with key "{}" already exists.\n\tIgnoring: {}'.format(key, xml_file), file=sys.stderr)
            return

        # to_bool = lambda s, d: d if s is None else s.lower() not in ('false', 'off', '0', '')
        def to_bool(s, d):
            if s is not None:
                return s.lower() not in ('false', 'off', '0', '')
            return d

        color = n.get('color') or ''
        try:
            chars_per_color = 2 if len(color) > 4 else 1
            tuple(int(color[o:o + 2], 16) / 255.0 for o in range(1, 3 * chars_per_color, chars_per_color))
        except ValueError:
            if color:  # no color is okay, default set in GUI
                print('Warning: Can\'t parse color code "{}" for domain "{}" '.format(color, key), file=sys.stderr)
                color = None

        self.domains[key] = dict(
            name=n.get('name') or key,
            multiple_sinks=to_bool(n.get('multiple_sinks'), True),
            multiple_sources=to_bool(n.get('multiple_sources'), False),
            color=color
        )
        for connection_n in n.get('connection', []):
            key = (connection_n.get('source_domain'), connection_n.get('sink_domain'))
            if not all(key):
                print('Warning: Empty domain key(s) in connection template.\n\t{}'.format(xml_file), file=sys.stderr)
            elif key in self.connection_templates:
                print('Warning: Connection template "{}" already exists.\n\t{}'.format(key, xml_file), file=sys.stderr)
            else:
                self.connection_templates[key] = connection_n.get('make') or ''

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
        checker = utils.SchemaChecker()
        passed = checker.run(data)
        for msg in checker.messages:
            print('{:<40s} {}'.format(os.path.basename(file_path), msg))
        if not passed:
            raise ValueError('YAML schema check failed for file: ' + file_path)

        key = data.pop('key').rstrip('_')

        if key in self.blocks:
            print('Warning: Block with key "{}" already exists.\n'
                  '\tIgnoring: {}'.format(key, file_path), file=sys.stderr)
            return

        # Store the block
        self.blocks[key] = block = self.get_new_block(self._flow_graph, key, **data)
        self._blocks_n[key] = data
        self._docstring_extractor.query(
            key,
            block.get_imports(raw=True),
            block.get_make(raw=True)
        )

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
        gen_opts = self.blocks['options'].get_param('generate_options')
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
        None: Block.Block,  # default
        'epy_block': Block.EPyBlock,
        '_dummy': Block.DummyBlock,
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

    def get_new_block(self, parent, key, **kwargs):
        cls = self.block_classes.get(key, self.block_classes[None])
        if not kwargs:
            kwargs = self._blocks_n[key]
        return cls(parent, key=key, **kwargs)

    def get_new_param(self, parent, **kwargs):
        cls = self.param_classes[kwargs.pop('cls_key', None)]
        return cls(parent, **kwargs)

    def get_new_port(self, parent, **kwargs):
        cls = self.port_classes[kwargs.pop('cls_key', None)]
        return cls(parent, **kwargs)
