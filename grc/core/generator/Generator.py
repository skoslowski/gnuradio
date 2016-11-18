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
import os
import tempfile
import operator
import collections

from Cheetah.Template import Template
import six

from .FlowGraphProxy import FlowGraphProxy
from .. import ParseXML, Messages
from ..Constants import (
    TOP_BLOCK_FILE_MODE, BLOCK_FLAG_NEED_QT_GUI,
    HIER_BLOCK_FILE_MODE, BLOCK_DTD
)
from ..utils import expr_utils

DATA_DIR = os.path.dirname(__file__)
FLOW_GRAPH_TEMPLATE = os.path.join(DATA_DIR, 'flow_graph.tmpl')


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

    def write(self):
        """generate output and write it to files"""
        # Do throttle warning
        throttling_blocks = [b for b in self._flow_graph.get_enabled_blocks()
                             if b.is_throtteling]
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
        # Generate
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
        output = list()

        fg = self._flow_graph
        title = fg.get_option('title') or fg.get_option('id').replace('_', ' ').title()
        imports = fg.get_imports()
        variables = fg.get_variables()
        parameters = fg.get_parameters()
        monitors = fg.get_monitors()

        # List of blocks not including variables and imports and parameters and disabled
        def _get_block_sort_text(block):
            code = block.get_make().replace(block.get_id(), ' ')
            try:
                code += block.params['gui_hint'].get_value()  # Newer gui markup w/ qtgui
            except:
                pass
            return code

        blocks_all = expr_utils.sort_objects(
            [b for b in fg.blocks if b.enabled and not b.get_bypassed()],
            operator.methodcaller('get_id'), _get_block_sort_text
        )
        deprecated_block_keys = set(b.name for b in blocks_all if b.is_deprecated)
        for key in deprecated_block_keys:
            Messages.send_warning("The block {!r} is deprecated.".format(key))

        # List of regular blocks (all blocks minus the special ones)
        blocks = [b for b in blocks_all if b not in imports and b not in parameters]

        for block in blocks:
            key = block.key
            file_path = os.path.join(self._dirname, block.get_id() + '.py')
            if key == 'epy_block':
                src = block.params['_source_code'].get_value()
                output.append((file_path, src))
            elif key == 'epy_module':
                src = block.params['source_code'].get_value()
                output.append((file_path, src))

        # Filter out bus and virtual sink connections
        connections = [con for con in fg.get_enabled_connections()
                       if not (con.is_bus() or con.sink_block.is_virtual_sink())]

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
        connections.sort(key=lambda c: (
            c.source_port.domain, c.sink_port.domain,
            c.source_block.get_id(), c.sink_block.get_id()
        ))

        connection_templates = fg.parent.connection_templates

        # List of variable names
        var_ids = [var.get_id() for var in parameters + variables]
        replace_dict = dict((var_id, 'self.' + var_id) for var_id in var_ids)
        callbacks_all = []
        for block in blocks_all:
            callbacks_all.extend(expr_utils.expr_replace(cb, replace_dict) for cb in block.get_callbacks())

        # Map var id to callbacks
        def uses_var_id():
            used = expr_utils.get_variable_dependencies(callback, [var_id])
            return used and 'self.' + var_id in callback  # callback might contain var_id itself

        callbacks = {}
        for var_id in var_ids:
            callbacks[var_id] = [callback for callback in callbacks_all if uses_var_id()]

        # Load the namespace
        namespace = {
            'title': title,
            'imports': imports,
            'flow_graph': fg,
            'variables': variables,
            'parameters': parameters,
            'monitors': monitors,
            'blocks': blocks,
            'connections': connections,
            'connection_templates': connection_templates,
            'generate_options': self._generate_options,
            'callbacks': callbacks,
        }
        # Build the template
        t = Template(open(FLOW_GRAPH_TEMPLATE, 'r').read(), namespace)
        output.append((self.file_path, "\n".join(line.rstrip() for line in str(t).split("\n"))))
        return output


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
            if name in (p.get_id() for p in parameters):
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
                    '{key}=${key}'.format(key=param.get_id()) for param in parameters
                ),
            )
        else:
            block_n['make'] = '{cls}()'.format(cls=block_key)
        # Callback data
        block_n['callback'] = [
            'set_{key}(${key})'.format(key=param.get_id()) for param in parameters
        ]

        # Parameters
        block_n['param'] = list()
        for param in parameters:
            param_n = collections.OrderedDict()
            param_n['name'] = param.params['label'].get_value() or param.get_id()
            param_n['key'] = param.get_id()
            param_n['value'] = param.params['value'].get_value()
            param_n['type'] = 'raw'
            param_n['hide'] = param.get_param('hide').get_value()
            block_n['param'].append(param_n)

        # Bus stuff
        if self._flow_graph.get_bussink():
            block_n['bus_sink'] = '1'
        if self._flow_graph.get_bussrc():
            block_n['bus_source'] = '1'

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

        # More bus stuff
        bus_struct_sink = self._flow_graph.get_bus_structure_sink()
        if bus_struct_sink:
            block_n['bus_structure_sink'] = bus_struct_sink[0].params['struct'].get_value()
        bus_struct_src = self._flow_graph.get_bus_structure_src()
        if bus_struct_src:
            block_n['bus_structure_source'] = bus_struct_src[0].params['struct'].get_value()

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
                block_n['flags'] = BLOCK_FLAG_NEED_QT_GUI

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
