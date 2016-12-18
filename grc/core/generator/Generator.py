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


from __future__ import absolute_import

import codecs
import collections
import operator
import os
import tempfile
import time
import textwrap

from mako.template import Template
import six

from .FlowGraphProxy import FlowGraphProxy
from .. import ParseXML, Messages
from ..Constants import (
    TOP_BLOCK_FILE_MODE,
    HIER_BLOCK_FILE_MODE,
    BLOCK_DTD
)
from ..utils import expr_utils

DATA_DIR = os.path.dirname(__file__)
FLOW_GRAPH_TEMPLATE = os.path.join(DATA_DIR, 'flow_graph.py.mako')
flow_graph_template = Template(filename=FLOW_GRAPH_TEMPLATE)


class Generator(object):
    """Adaptor for various generators (uses generate_options)"""

    def __init__(self, flow_graph, file_path):
        """
        Initialize the generator object.
        Determine the file to generate.

        Args:
            flow_graph: the flow graph object
            file_path: the path to the grc file
        """
        self.generate_options = flow_graph.get_option('generate_options')
        if self.generate_options == 'hb':
            generator_cls = HierBlockGenerator
        elif self.generate_options == 'hb_qt_gui':
            generator_cls = QtHierBlockGenerator
        else:
            generator_cls = TopBlockGenerator

        self._generator = generator_cls(flow_graph, file_path)

    def __getattr__(self, item):
        """get all other attrib from actual generator object"""
        return getattr(self._generator, item)


class TopBlockGenerator(object):

    def __init__(self, flow_graph, file_path):
        """
        Initialize the top block generator object.

        Args:
            flow_graph: the flow graph object
            file_path: the path to write the file to
        """
        self._flow_graph = FlowGraphProxy(flow_graph)
        self._generate_options = self._flow_graph.get_option('generate_options')
        self._mode = TOP_BLOCK_FILE_MODE
        dirname = os.path.dirname(file_path)
        # Handle the case where the directory is read-only
        # In this case, use the system's temp directory
        if not os.access(dirname, os.W_OK):
            dirname = tempfile.gettempdir()
        filename = self._flow_graph.get_option('id') + '.py'
        self.file_path = os.path.join(dirname, filename)
        self._dirname = dirname

    def _warnings(self):
        throttling_blocks = [b for b in self._flow_graph.get_enabled_blocks()
                             if b.flags.throttle]
        if not throttling_blocks and not self._generate_options.startswith('hb'):
            Messages.send_warning("This flow graph may not have flow control: "
                                  "no audio or RF hardware blocks found. "
                                  "Add a Misc->Throttle block to your flow "
                                  "graph to avoid CPU congestion.")
        if len(throttling_blocks) > 1:
            keys = set([b.key for b in throttling_blocks])
            if len(keys) > 1 and 'blocks_throttle' in keys:
                Messages.send_warning("This flow graph contains a throttle "
                                      "block and another rate limiting block, "
                                      "e.g. a hardware source or sink. "
                                      "This is usually undesired. Consider "
                                      "removing the throttle block.")

        deprecated_block_keys = {b.name for b in self._flow_graph.get_enabled_blocks() if b.flags.deprecated}
        for key in deprecated_block_keys:
            Messages.send_warning("The block {!r} is deprecated.".format(key))

    def write(self):
        """generate output and write it to files"""
        self._warnings()

        for filename, data in self._build_python_code_from_template():
            with codecs.open(filename, 'w', encoding='utf-8') as fp:
                fp.write(data)
            if filename == self.file_path:
                try:
                    os.chmod(filename, self._mode)
                except:
                    pass

    def _build_python_code_from_template(self):
        """
        Convert the flow graph to python code.

        Returns:
            a string of python code
        """
        output = []

        fg = self._flow_graph
        title = fg.get_option('title') or fg.get_option('id').replace('_', ' ').title()
        variables = fg.get_variables()
        parameters = fg.get_parameters()
        monitors = fg.get_monitors()

        for block in fg.iter_enabled_blocks():
            key = block.key
            file_path = os.path.join(self._dirname, block.name + '.py')
            if key == 'epy_block':
                src = block.params['_source_code'].get_value()
                output.append((file_path, src))
            elif key == 'epy_module':
                src = block.params['source_code'].get_value()
                output.append((file_path, src))

        namespace = {
            'flow_graph': fg,
            'variables': variables,
            'parameters': parameters,
            'monitors': monitors,
            'generate_options': self._generate_options,
            'generated_time': time.ctime(),
        }
        flow_graph_code = flow_graph_template.render(
            title=title,
            imports=self._imports(),
            blocks=self._blocks(),
            callbacks=self._callbacks(),
            connections=self._connections(),
            **namespace
        )
        # strip trailing white-space
        flow_graph_code = "\n".join(line.rstrip() for line in flow_graph_code.split("\n"))

        output.append((self.file_path, flow_graph_code))
        return output

    def _imports(self):
        fg = self._flow_graph
        imports = fg.imports()
        seen = set()
        deduplicate = []

        need_path_hack = any(imp.endswith("# grc-generated hier_block") for imp in imports)
        if need_path_hack:
            deduplicate.insert(0, textwrap.dedent("""\
                import os
                import sys
                sys.path.append(os.environ.get('GRC_HIER_PATH', os.path.expanduser('~/.grc_gnuradio')))
            """))
            seen.add('import os')
            seen.add('import sys')

        if fg.get_option('qt_qss_theme'):
            imports.append('import os')
            imports.append('import sys')

        if fg.get_option('thread_safe_setters'):
            imports.append('import threading')

        def is_duplicate(l):
            if l.startswith('import') or l.startswith('from') and l in seen:
                return True
            seen.add(line)
            return False

        for imp in sorted(imports):
            for line in imp.split('\n'):
                line = line.rstrip()
                if not is_duplicate(line):
                    deduplicate.append(line)

        return deduplicate

    def _blocks(self):
        fg = self._flow_graph
        parameters = fg.get_parameters()

        # List of blocks not including variables and imports and parameters and disabled
        def _get_block_sort_text(block):
            code = block.templates.render('make').replace(block.name, ' ')
            try:
                code += block.params['gui_hint'].get_value()  # Newer gui markup w/ qtgui
            except:
                pass
            return code

        blocks = [
            b for b in fg.blocks
            if b.enabled and not (b.get_bypassed() or b.is_import or b in parameters or b.key == 'options')
        ]

        blocks = expr_utils.sort_objects(blocks, operator.attrgetter('name'), _get_block_sort_text)
        blocks_make = []
        for block in blocks:
            make = block.templates.render('make')
            if not block.is_variable:
                make = 'self.' + block.name + ' = ' + make
            blocks_make.append((block, make))
        return blocks_make

    def _callbacks(self):
        fg = self._flow_graph
        variables = fg.get_variables()
        parameters = fg.get_parameters()

        # List of variable names
        var_ids = [var.name for var in parameters + variables]
        replace_dict = dict((var_id, 'self.' + var_id) for var_id in var_ids)
        callbacks_all = []
        for block in fg.iter_enabled_blocks():
            callbacks_all.extend(expr_utils.expr_replace(cb, replace_dict) for cb in block.get_callbacks())

        # Map var id to callbacks
        def uses_var_id():
            used = expr_utils.get_variable_dependencies(callback, [var_id])
            return used and 'self.' + var_id in callback  # callback might contain var_id itself

        callbacks = {}
        for var_id in var_ids:
            callbacks[var_id] = [callback for callback in callbacks_all if uses_var_id()]

        return callbacks

    def _connections(self):
        fg = self._flow_graph
        templates = {key: Template(text)
                     for key, text in fg.parent_platform.connection_templates.items()}

        def make_port_sig(port):
            if port.parent.key in ('pad_source', 'pad_sink'):
                block = 'self'
                key = fg.get_pad_port_global_key(port)
            else:
                block = 'self.' + port.parent_block.name
                key = port.key

            if not key.isdigit():
                key = repr(key)

            return '({block}, {key})'.format(block=block, key=key)

        connections = fg.get_enabled_connections()

        # Get the virtual blocks and resolve their connections
        connection_factory = fg.parent_platform.Connection
        virtual = [c for c in connections if c.source_block.is_virtual_source()]
        for connection in virtual:
            sink = connection.sink_port
            for source in connection.source_port.resolve_virtual_source():
                resolved = connection_factory(fg.orignal_flowgraph, source, sink)
                connections.append(resolved)
            # Remove the virtual connection
            connections.remove(connection)

        # Bypassing blocks: Need to find all the enabled connections for the block using
        # the *connections* object rather than get_connections(). Create new connections
        # that bypass the selected block and remove the existing ones. This allows adjacent
        # bypassed blocks to see the newly created connections to downstream blocks,
        # allowing them to correctly construct bypass connections.
        bypassed_blocks = fg.get_bypassed_blocks()
        for block in bypassed_blocks:
            # Get the upstream connection (off of the sink ports)
            # Use *connections* not get_connections()
            source_connection = [c for c in connections if c.sink_port == block.sinks[0]]
            # The source connection should never have more than one element.
            assert (len(source_connection) == 1)

            # Get the source of the connection.
            source_port = source_connection[0].source_port

            # Loop through all the downstream connections
            for sink in (c for c in connections if c.source_port == block.sources[0]):
                if not sink.enabled:
                    # Ignore disabled connections
                    continue
                connection = connection_factory(fg.orignal_flowgraph, source_port, sink.sink_port)
                connections.append(connection)
                # Remove this sink connection
                connections.remove(sink)
            # Remove the source connection
            connections.remove(source_connection[0])

        # List of connections where each endpoint is enabled (sorted by domains, block names)
        def by_domain_and_blocks(c):
            return c.type, c.source_block.name, c.sink_block.name

        rendered = []
        for con in sorted(connections, key=by_domain_and_blocks):
            template = templates[con.type]
            code = template.render(make_port_sig=make_port_sig, source=con.source_port, sink=con.sink_port)
            rendered.append(code)

        return rendered


class HierBlockGenerator(TopBlockGenerator):
    """Extends the top block generator to also generate a block XML file"""

    def __init__(self, flow_graph, file_path):
        """
        Initialize the hier block generator object.

        Args:
            flow_graph: the flow graph object
            file_path: where to write the py file (the xml goes into HIER_BLOCK_LIB_DIR)
        """
        TopBlockGenerator.__init__(self, flow_graph, file_path)
        platform = flow_graph.parent

        hier_block_lib_dir = platform.config.hier_block_lib_dir
        if not os.path.exists(hier_block_lib_dir):
            os.mkdir(hier_block_lib_dir)

        self._mode = HIER_BLOCK_FILE_MODE
        self.file_path = os.path.join(hier_block_lib_dir, self._flow_graph.get_option('id') + '.py')
        self.file_path_xml = self.file_path + '.xml'

    def write(self):
        """generate output and write it to files"""
        TopBlockGenerator.write(self)
        ParseXML.to_file(self._build_block_n_from_flow_graph_io(), self.file_path_xml)
        ParseXML.validate_dtd(self.file_path_xml, BLOCK_DTD)
        try:
            os.chmod(self.file_path_xml, self._mode)
        except:
            pass

    def _build_block_n_from_flow_graph_io(self):
        """
        Generate a block XML nested data from the flow graph IO

        Returns:
            a xml node tree
        """
        # Extract info from the flow graph
        block_key = self._flow_graph.get_option('id')
        parameters = self._flow_graph.get_parameters()

        def var_or_value(name):
            if name in (p.name for p in parameters):
                return "$" + name
            return name

        # Build the nested data
        block_n = collections.OrderedDict()
        block_n['name'] = self._flow_graph.get_option('title') or \
            self._flow_graph.get_option('id').replace('_', ' ').title()
        block_n['key'] = block_key
        block_n['category'] = self._flow_graph.get_option('category')
        block_n['import'] = "from {0} import {0}  # grc-generated hier_block".format(
            self._flow_graph.get_option('id'))
        # Make data
        if parameters:
            block_n['make'] = '{cls}(\n    {kwargs},\n)'.format(
                cls=block_key,
                kwargs=',\n    '.join(
                    '{key}=${key}'.format(key=param.name) for param in parameters
                ),
            )
        else:
            block_n['make'] = '{cls}()'.format(cls=block_key)
        # Callback data
        block_n['callback'] = [
            'set_{key}(${key})'.format(key=param.name) for param in parameters
        ]

        # Parameters
        block_n['param'] = list()
        for param in parameters:
            param_n = collections.OrderedDict()
            param_n['name'] = param.params['label'].get_value() or param.name
            param_n['key'] = param.name
            param_n['value'] = param.params['value'].get_value()
            param_n['type'] = 'raw'
            param_n['hide'] = param.get_param('hide').get_value()
            block_n['param'].append(param_n)

        # Sink/source ports
        for direction in ('sink', 'source'):
            block_n[direction] = list()
            for port in self._flow_graph.get_hier_block_io(direction):
                port_n = collections.OrderedDict()
                port_n['name'] = port['label']
                port_n['type'] = port['type']
                if port['type'] != "message":
                    port_n['vlen'] = var_or_value(port['vlen'])
                if port['optional']:
                    port_n['optional'] = '1'
                block_n[direction].append(port_n)

        # Documentation
        block_n['doc'] = "\n".join(field for field in (
            self._flow_graph.get_option('author'),
            self._flow_graph.get_option('description'),
            self.file_path
        ) if field)
        block_n['grc_source'] = str(self._flow_graph.grc_file_path)

        n = {'block': block_n}
        return n


class QtHierBlockGenerator(HierBlockGenerator):

    def _build_block_n_from_flow_graph_io(self):
        n = HierBlockGenerator._build_block_n_from_flow_graph_io(self)
        block_n = collections.OrderedDict()

        # insert flags after category
        for key, value in six.iteritems(n['block']):
            block_n[key] = value
            if key == 'category':
                block_n['flags'] = 'need_qt_gui'

        if not block_n['name'].upper().startswith('QT GUI'):
            block_n['name'] = 'QT GUI ' + block_n['name']

        gui_hint_param = collections.OrderedDict()
        gui_hint_param['name'] = 'GUI Hint'
        gui_hint_param['key'] = 'gui_hint'
        gui_hint_param['value'] = ''
        gui_hint_param['type'] = 'gui_hint'
        gui_hint_param['hide'] = 'part'
        block_n['param'].append(gui_hint_param)

        block_n['make'] += (
            "\n#set $win = 'self.%s' % $id"
            "\n${gui_hint()($win)}"
        )

        return {'block': block_n}
