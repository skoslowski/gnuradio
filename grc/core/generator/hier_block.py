import collections
import os

import six

from .top_block import TopBlockGenerator

from .. import ParseXML, Constants


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

        self._mode = Constants.HIER_BLOCK_FILE_MODE
        self.file_path = os.path.join(hier_block_lib_dir, self._flow_graph.get_option('id') + '.py')
        self.file_path_xml = self.file_path + '.xml'

    def write(self):
        """generate output and write it to files"""
        TopBlockGenerator.write(self)
        ParseXML.to_file(self._build_block_n_from_flow_graph_io(), self.file_path_xml)
        ParseXML.validate_dtd(self.file_path_xml, Constants.BLOCK_DTD)
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
            param_n['hide'] = param.params['hide'].get_value()
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
