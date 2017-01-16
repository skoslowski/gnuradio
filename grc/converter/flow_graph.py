# Copyright 2017 Free Software Foundation, Inc.
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

from __future__ import absolute_import, division

from collections import OrderedDict

from . import xml, yaml


def from_xml(filename):
    """Load flow graph from xml file"""
    element, version_info = xml.load(filename, 'flow_graph.dtd')

    data = convert_flow_graph_xml(element)

    return data


dump = yaml.dump


def convert_flow_graph_xml(node):
    blocks = OrderedDict()
    for block in node.findall('block'):
        block_id = block.findtext('key')
        params = {
            param.findtext('key'): param.findtext('value')
            for param in block.findall('param')
        }
        blocks[block_id] = params

    options = blocks.pop('options')

    connections = [
        yaml.ListFlowing([
            connection.findtext('source_block_id'),
            connection.findtext('source_key'),
            connection.findtext('sink_block_id'),
            connection.findtext('sink_key')
        ])
        for connection in node.findall('connection')
    ]

    flow_graph = OrderedDict()
    flow_graph['options'] = options
    flow_graph['blocks'] = blocks
    flow_graph['connections'] = connections
    return flow_graph
