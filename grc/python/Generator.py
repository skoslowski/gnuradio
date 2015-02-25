"""
Copyright 2008-2011 Free Software Foundation, Inc.
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

import os
import sys
import tempfile
import runpy
import glob
from zipfile import ZipFile
from Cheetah.Template import Template

from .. gui import Messages
from .. base import ParseXML
from .. base import odict

from . Constants import TOP_BLOCK_FILE_MODE, FLOW_GRAPH_TEMPLATE, \
    HIER_BLOCK_FILE_MODE, HIER_BLOCKS_LIB_DIR, BLOCK_DTD
from . import expr_utils


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
        self._generate_options = flow_graph.get_option('generate_options')
        if self._generate_options == 'hb':
            self._generator = HierBlockGenerator(flow_graph, file_path)
        else:
            self._generator = TopBlockGenerator(flow_graph, file_path)

    def get_generate_options(self):
        return self._generate_options

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
        self._flow_graph = flow_graph
        self._generate_options = self._flow_graph.get_option('generate_options')
        self._mode = TOP_BLOCK_FILE_MODE
        dirname = os.path.dirname(file_path)
        # handle the case where the directory is read-only
        # in this case, use the system's temp directory
        if not os.access(dirname, os.W_OK):
            dirname = tempfile.gettempdir()
        filename = self._flow_graph.get_option('id') + '.py'
        self._file_path = os.path.join(dirname, filename)

    def get_file_path(self):
        return self._file_path

    def write(self):
        """generate output and write it to files"""
        # do throttle warning
        throttling_blocks = filter(lambda b: b.throttle(), self._flow_graph.get_enabled_blocks())
        if not throttling_blocks and self._generate_options != 'hb':
            Messages.send_warning("This flow graph may not have flow control: "
                                  "no audio or RF hardware blocks found. "
                                  "Add a Misc->Throttle block to your flow "
                                  "graph to avoid CPU congestion.")
        if len(throttling_blocks) > 1:
            keys = set(map(lambda b: b.get_key(), throttling_blocks))
            if len(keys) > 1 and 'blocks_throttle' in keys:
                Messages.send_warning("This flow graph contains a throttle "
                                      "block and another rate limiting block, "
                                      "e.g. a hardware source or sink. "
                                      "This is usually undesired. Consider "
                                      "removing the throttle block.")
        # generate
        with open(self.get_file_path(), 'w') as fp:
            fp.write(self._build_python_code_from_template())
        try:
            os.chmod(self.get_file_path(), self._mode)
        except:
            pass

    def _build_python_code_from_template(self):
        """
        Convert the flow graph to python code.

        Returns:
            a string of python code
        """
        title = self._flow_graph.get_option('title') or self._flow_graph.get_option('id').replace('_', ' ').title()
        imports = self._flow_graph.get_imports()
        variables = self._flow_graph.get_variables()
        parameters = self._flow_graph.get_parameters()
        monitors = self._flow_graph.get_monitors()

        # list of blocks not including variables and imports and parameters and disabled
        def _get_block_sort_text(block):
            code = block.get_make().replace(block.get_id(), ' ')
            try:
                code += block.get_param('notebook').get_value() # older gui markup w/ wxgui
            except:
                pass
            try:
                code += block.get_param('gui_hint').get_value() # newer gui markup w/ qtgui
            except:
                pass
            return code
        blocks = expr_utils.sort_objects(
            self._flow_graph.get_enabled_blocks(),
            lambda b: b.get_id(), _get_block_sort_text
        )
        # list of regular blocks (all blocks minus the special ones)
        blocks = filter(lambda b: b not in (imports + parameters), blocks)
        # list of connections where each endpoint is enabled (sorted by domains, block names)
        connections = filter(lambda c: not (c.is_bus() or c.is_msg()), self._flow_graph.get_enabled_connections())
        connections.sort(key=lambda c: (
            c.get_source().get_domain(), c.get_sink().get_domain(),
            c.get_source().get_parent().get_id(), c.get_sink().get_parent().get_id()
        ))
        connection_templates = self._flow_graph.get_parent().get_connection_templates()
        msgs = filter(lambda c: c.is_msg(), self._flow_graph.get_enabled_connections())
        # list of variable names
        var_ids = [var.get_id() for var in parameters + variables]
        # prepend self.
        replace_dict = dict([(var_id, 'self.%s' % var_id) for var_id in var_ids])
        # list of callbacks
        callbacks = [
            expr_utils.expr_replace(cb, replace_dict)
            for cb in sum([block.get_callbacks() for block in self._flow_graph.get_enabled_blocks()], [])
        ]
        # map var id to callbacks
        var_id2cbs = dict([
            (var_id, filter(lambda c: expr_utils.get_variable_dependencies(c, [var_id]), callbacks))
            for var_id in var_ids
        ])
        # load the namespace
        namespace = {
            'title': title,
            'imports': imports,
            'flow_graph': self._flow_graph,
            'variables': variables,
            'parameters': parameters,
            'monitors': monitors,
            'blocks': blocks,
            'connections': connections,
            'connection_templates': connection_templates,
            'msgs': msgs,
            'generate_options': self._generate_options,
            'var_id2cbs': var_id2cbs,
        }
        # build the template
        t = Template(open(FLOW_GRAPH_TEMPLATE, 'r').read(), namespace)
        return str(t)

    def write_zipped_module(self, platform):
        """
        Bundle the generated flowgraph and its depending grc-generated modules
        into a single zip file for remote execution. Dependencies are found
        in the flowgraph's path and the hier block library path

        Args:
            platform: platform instance to get local GNU radio version

        Return:
            file path to generated zip file
        """
        file_path = self.get_file_path()
        zfile_path = file_path.replace('.py', '.zip')
        Messages.send_start_gen(zfile_path)
        # run the flowgraph (not as __main__) and observe imports
        try:
            with ImportLogger(os.path.dirname(file_path)) as local_blocks:
                with ImportLogger(HIER_BLOCKS_LIB_DIR) as hier_block_list:
                    runpy.run_path(self.get_file_path())
        except Exception:
            Messages.send("    Warning: failed to determine imports\n")
            local_blocks = hier_block_list = []

        zfile = ZipFile(zfile_path, mode="w")
        # the bootstrap code
        zfile.writestr('__main__.py', ZIPPED_MODULE_BOOTSTRAP_TEMPLATE.format(
            major_version=platform.get_version_major(),
            api_version=platform.get_version_api(),
            minor_version=platform.get_version_minor(),
            version_full=platform.get_version()
        ))
        # the flowgraph as module main
        Messages.send("    adding {0!r} as 'main.py'\n".format(file_path))
        zfile.write(file_path, 'main.py')
        # any file found by the import loggers
        for dependency in (local_blocks + hier_block_list):
            name = os.path.basename(dependency)
            if name not in zfile.namelist():
                Messages.send("    adding {0!r}\n".format(dependency))
                zfile.write(dependency, name)
            else:  # already have file with that name
                Messages.send("    skipping {0!r} (duplicate name)".format(
                    dependency))
        zfile.close()
        return zfile_path


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
        self._mode = HIER_BLOCK_FILE_MODE
        self._file_path = os.path.join(HIER_BLOCKS_LIB_DIR,
                                       self._flow_graph.get_option('id') + '.py')
        self._file_path_xml = self._file_path + '.xml'

    def get_file_path_xml(self):
        return self._file_path_xml

    def write(self):
        """generate output and write it to files"""
        TopBlockGenerator.write(self)
        ParseXML.to_file(self._build_block_n_from_flow_graph_io(), self.get_file_path_xml())
        ParseXML.validate_dtd(self.get_file_path_xml(), BLOCK_DTD)
        try:
            os.chmod(self.get_file_path_xml(), self._mode)
        except:
            pass

    def _build_block_n_from_flow_graph_io(self):
        """
        Generate a block XML nested data from the flow graph IO

        Returns:
            a xml node tree
        """
        # extract info from the flow graph
        block_key = self._flow_graph.get_option('id')
        parameters = self._flow_graph.get_parameters()

        def var_or_value(name):
            if name in map(lambda p: p.get_id(), parameters):
                return "$"+name
            return name

        # build the nested data
        block_n = odict()
        block_n['name'] = self._flow_graph.get_option('title') or \
            self._flow_graph.get_option('id').replace('_', ' ').title()
        block_n['key'] = block_key
        block_n['category'] = self._flow_graph.get_option('category')
        block_n['import'] = "from {0} import {0}  # grc-generated hier_block".format(
            self._flow_graph.get_option('id'))
        # make data
        if parameters:
            block_n['make'] = '{cls}(\n    {kwargs},\n)'.format(
                cls=block_key,
                kwargs=',\n    '.join(
                    '{key}=${key}'.format(key=param.get_id()) for param in parameters
                ),
            )
        else:
            block_n['make'] = '{cls}()'.format(cls=block_key)
        # callback data
        block_n['callback'] = [
            'set_{key}(${key})'.format(key=param.get_id()) for param in parameters
        ]

        # Parameters
        block_n['param'] = list()
        for param in parameters:
            param_n = odict()
            param_n['name'] = param.get_param('label').get_value() or param.get_id()
            param_n['key'] = param.get_id()
            param_n['value'] = param.get_param('value').get_value()
            param_n['type'] = 'raw'
            block_n['param'].append(param_n)

        # bus stuff
        if self._flow_graph.get_bussink():
            block_n['bus_sink'] = '1'
        if self._flow_graph.get_bussrc():
            block_n['bus_source'] = '1'

        # sink/source ports
        for direction in ('sink', 'source'):
            block_n[direction] = list()
            for port in self._flow_graph.get_hier_block_io(direction):
                port_n = odict()
                port_n['name'] = port['label']
                port_n['type'] = port['type']
                if port['type'] != "message":
                    port_n['vlen'] = var_or_value(port['vlen'])
                if port['optional']:
                    port_n['optional'] = '1'
                block_n[direction].append(port_n)

        # more bus stuff
        bus_struct_sink = self._flow_graph.get_bus_structure_sink()
        if bus_struct_sink:
            block_n['bus_structure_sink'] = bus_struct_sink[0].get_param('struct').get_value()
        bus_struct_src = self._flow_graph.get_bus_structure_src()
        if bus_struct_src:
            block_n['bus_structure_source'] = bus_struct_src[0].get_param('struct').get_value()

        # documentation
        block_n['doc'] = "\n".join(field for field in (
            self._flow_graph.get_option('author'),
            self._flow_graph.get_option('description'),
            self.get_file_path()
        ) if field)
        block_n['grc_source'] = str(self._flow_graph.grc_file_path)

        n = {'block': block_n}
        return n


ZIPPED_MODULE_BOOTSTRAP_TEMPLATE = """
try:
    from gnuradio import gr
    version = gr.major_version(), gr.api_version(), gr.minor_version()
    message = "This package was generated with GNU Radio {{0}}. " \
              "Running on version {{1}}.".format({version_full!r}, gr.version())
    if (gr.major_version(), gr.api_version()) != ({major_version!r}, {api_version!r}):
        print "Error: ", message
        exit(1)
    if gr.minor_version() != {minor_version!r}:
        print "Warning:", message, "\\n"
except ImportError:
    print "Error: Cannot import GNU Radio"
    exit(1)
except AttributeError:
    print "Error: Cannot determine GNU Radio version"
    exit(1)

import runpy
runpy.run_module('main', run_name='__main__')
"""


class ImportLogger:
    def __init__(self, directory):
        self.modules = modules = dict()
        for file_path in glob.iglob(os.path.join(directory, '*.py')):
            fullname = os.path.basename(file_path)[:-3]
            modules[fullname] = file_path

        self.log = []

    def find_module(self, fullname, path):
        if fullname in self.modules:
            self.log.append(self.modules[fullname])

    def __enter__(self):
        sys.meta_path.insert(0, self)
        return self.log

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.meta_path.remove(self)
        return
