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
Converter for legacy block definitions in XML format

- Cheetah expressions that can not be converted are passed to Cheetah for now
- Instead of generating a Block subclass directly a string representation is
  used and evaluated. This is slower / lamer but allows us to show the user
  how a converted definition would look like
"""

from __future__ import absolute_import, division, print_function

from collections import OrderedDict, defaultdict
import itertools

import yaml
from lxml import etree
from os import path

from .yaml_output import ListFlowing, scalar_node, GRCDumper
from . import cheetah_converter

from .. import Constants


BLOCK_DTD = etree.DTD(path.join(path.dirname(__file__), 'domain.dtd'))
reserved_block_keys = ('import', )  # todo: add more keys


def convert_xml(xml_file):
    """Load block description from xml file"""

    try:
        xml = etree.parse(xml_file).getroot()
        BLOCK_DTD.validate(xml)
    except etree.LxmlError:
        return
    try:
        data = convert_domain_xml(xml)
    except NameError:
        print('Broken XML', xml_file)
        raise

    out = yaml.dump(data, default_flow_style=False, indent=4, Dumper=GRCDumper)

    # replace = [
    #     ('parameters:', '\nparameters:'),
    #     ('inputs:', '\ninputs:'),
    #     ('outputs:', '\noutputs:'),
    #     ('templates:', '\ntemplates:'),
    #     ('documentation:', '\ndocumentation:'),
    # ]
    # for r in replace:
    #     out = out.replace(*r)

    return data['id'], out

no_value = object()
dummy = cheetah_converter.DummyConverter()


def convert_domain_xml(node):
    converter = cheetah_converter.Converter(names={
        param_node.findtext('key'): {
            opt_node.text.split(':')[0]
            for opt_node in next(param_node.getiterator('option'), param_node).getiterator('opt')
        } for param_node in node.getiterator('param')
    })

    data = OrderedDict()
    data['id'] = node.findtext('key')
    data['label'] = node.findtext('name') or no_value
    data['color'] = node.findtext('color') or no_value

    return OrderedDict((key, value) for key, value in data.items() if value is not no_value)