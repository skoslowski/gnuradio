# Copyright 2016 Free Software Foundation, Inc.
# This file is part of GNU Radio
#
# GNU Radio Companion is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# GNU Radio Companion is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""
Converter for legacy block tree definitions in XML format
"""

from __future__ import absolute_import, division, print_function

from os import path

import yaml
from lxml import etree

from .yaml_output import GRCDumper


BLOCK_TREE_DTD = etree.DTD(path.join(path.dirname(__file__), 'block_tree.dtd'))


def from_xml(xml_file):
    """Load block tree description from xml file"""

    try:
        xml = etree.parse(xml_file).getroot()
        BLOCK_TREE_DTD.validate(xml)
    except etree.LxmlError:
        return
    try:
        data = convert_category_node(xml)
    except NameError:
        print('Broken XML', xml_file)
        raise

    return data


def dump(data, fp):
    fp.write(yaml.dump(data, default_flow_style=False, indent=4, Dumper=GRCDumper))


def convert_category_node(node):
    """convert nested <cat> tags to nested lists dicts"""
    assert node.tag == 'cat'
    name, elements = '', []
    for child in node:
        if child.tag == 'name':
            name = child.text.strip()
        elif child.tag == 'block':
            elements.append(child.text.strip())
        elif child.tag == 'cat':
            elements.append(convert_category_node(child))
    return {name: elements}
