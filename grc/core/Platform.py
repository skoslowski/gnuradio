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

from . import ParseXML, Messages, Constants

from .Config import Config
from .Element import Element
from .generator import Generator
from .FlowGraph import FlowGraph
from .Connection import Connection
from . import Block
from .Port import Port, PortClone
from .Param import Param

from .utils import extract_docs


class Platform(Element):

    is_platform = True

    def __init__(self, *args, **kwargs):
        """ Make a platform for GNU Radio """
        Element.__init__(self, parent=None)

        self.config = self.Config(*args, **kwargs)
        self.block_docstrings = {}
        self.block_docstrings_loaded_callback = lambda: None  # dummy to be replaced by BlockTreeWindow

        self._docstring_extractor = extract_docs.SubprocessLoader(
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
            self.load_block_xml(generator.file_path_xml)
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
        ParseXML.xml_failures.clear()

        # Try to parse and load blocks
        for file_path in self.iter_yml_files():
            try:
                if file_path.endswith('.block.yml'):
                    self.load_block_description()
            except Exception as e:
                raise

        for xml_file in self.iter_xml_files():
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

    def iter_xml_files(self):
        """Iterator for block descriptions and category trees"""
        for block_path in self.config.block_paths:
            if os.path.isfile(block_path):
                yield block_path
            elif os.path.isdir(block_path):
                for dirpath, dirnames, filenames in os.walk(block_path):
                    for filename in sorted(f for f in filenames if f.endswith('.xml')):
                        yield os.path.join(dirpath, filename)

    @staticmethod
    def _adapt_block(n):
        if n.pop('throttle', ''):
            flags = n.setdefault('flags', '')
            n['flags'] = flags + ' ' + Constants.BLOCK_FLAG_THROTTLE

        # renames
        for name in 'import check callback param sink source'.split():
            n[name + 's'] = n.pop(name, [])
        n['documentation'] = n.pop('doc', '')
        n['value'] = n.pop('var_value', '$value' if n['key'].startswith('variable') else '')

        for pn in n['params']:
            pn['dtype'] = pn.pop('type', '')
            category = pn.pop('tab', None)
            if category:
                pn['category'] = category
            pn['options'] = options = pn.pop('option', [])
            for on in options:
                on['value'] = on.pop('key')
                try:
                    on['extra'] = dict(opt.split(':') for opt in on.pop('opt', []))
                except TypeError:
                    raise ValueError('Error separating opts into key:value')

        for pn in (n['sinks'] + n['sources']):
            pn['dtype'] = pn.pop('type', '')
            if pn['dtype'] == 'message':
                pn['domain'] = Constants.GR_MESSAGE_DOMAIN

    def load_block_xml(self, xml_file):
        """Load block description from xml file"""
        # Validate and import
        ParseXML.validate_dtd(xml_file, Constants.BLOCK_DTD)
        n = ParseXML.from_file(xml_file).get('block', {})
        n['block_wrapper_path'] = xml_file  # inject block wrapper path
        self._adapt_block(n)
        key = n.pop('key')

        if key in self.blocks:
            print('Warning: Block with key "{}" already exists.\n'
                  '\tIgnoring: {}'.format(key, xml_file), file=sys.stderr)
            return

        # Store the block
        self.blocks[key] = block = self.get_new_block(self._flow_graph, key, **n)
        self._blocks_n[key] = n
        self._docstring_extractor.query(
            key,
            block.get_imports(raw=True),
            block.get_make(raw=True)
        )

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
    def iter_yml_files(self):
        """Iterator for block descriptions and category trees"""
        for block_path in self.config.block_paths:
            if os.path.isfile(block_path):
                yield block_path
            elif os.path.isdir(block_path):
                pattern = os.path.join(block_path, '**.yml')
                yield_from = glob.iglob(pattern)
                for file_path in yield_from:
                    yield file_path

    def load_block_description(self):
        pass

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
