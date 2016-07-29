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

from collections import OrderedDict

import yaml
from lxml import etree
from os import path

from .yaml_output import OrderedDictFlowing, scalar_node, GRCDumper
from . import cheetah_converter


BLOCK_DTD = etree.DTD(path.join(path.dirname(__file__), '..', 'block.dtd'))
reserved_block_keys = ('import', )  # todo: add more keys


def convert_xml(xml_file):
    """Load block description from xml file"""

    try:
        xml = etree.parse(xml_file).getroot()
        BLOCK_DTD.validate(xml)
    except etree.LxmlError:
        return

    data = convert_block_xml(xml)
    out = yaml.dump(data, default_flow_style=False, indent=4, Dumper=GRCDumper)

    replace = [
        ('params:', '\nparams:'),
        ('sinks:', '\nsinks:'),
        ('sources:', '\nsources:'),
        ('import:', '\nimport:'),
        ('documentation:', '\ndocumentation:'),
    ]
    for r in replace:
        out = out.replace(*r)

    return out


def convert_block_xml(node):
    no_value = object()

    converter = cheetah_converter.Converter(names={
        param_node.findtext('key'): {
            opt_node.text.split(':')[0]
            for opt_node in next(param_node.getiterator('option'), param_node).getiterator('opt')
        } for param_node in node.getiterator('param')
    })

    key = node.findtext('key')
    if key in reserved_block_keys:
        key += '_'

    data = OrderedDict()
    data['key'] = key
    data['name'] = node.findtext('name') or no_value
    data['category'] = node.findtext('category') or no_value

    data['params'] = [convert_param_xml(param_node, converter)
                      for param_node in node.getiterator('param')] or no_value
    # data['params'] = {p.pop('key'): p for p in data['params']}

    data['sinks'] = [convert_port_xml(port_node, converter)
                     for port_node in node.getiterator('sink')] or no_value

    data['sources'] = [convert_port_xml(port_node, converter)
                       for port_node in node.getiterator('source')] or no_value

    imports = [converter.to_mako(import_node.text)
               for import_node in node.getiterator('import')]
    if imports:
        data['imports'] = (imports if len(imports) > 1 else imports[0]) or no_value

    make = node.findtext('make') or ''
    if '\n' in make:
        make = converter.to_mako(make)
        data['make'] = scalar_node(make, style='|' if '\n' in make else None)
    else:
        data['make'] = converter.to_mako(make) or no_value

    data['callbacks'] = [] or no_value # todo

    docs = node.findtext('doc')
    if docs:
        docs = docs.strip().replace('\\\n', '').replace('\n\n', '\n')
        data['documentation'] = scalar_node(docs, style='>')

    return OrderedDict((key, value) for key, value in data.items() if value is not no_value)


def convert_param_xml(node, converter):
    param = OrderedDict()
    param['key'] = node.findtext('key').strip()
    param['name'] = node.findtext('name').strip()
    param['dtype'] = converter.to_python(node.findtext('type') or '')

    value = node.findtext('value')
    if value:
        param['value'] = value

    # todo: parse hide, tab tags

    options = []
    for option_n in node.getiterator('option'):
        option = OrderedDict()
        option['name'] = option_n.findtext('name')
        option['value'] = option_n.findtext('key')

        opts = (opt.text for opt in option_n.getiterator('opt'))
        option['attributes'] = OrderedDictFlowing(
            opt_n.split(':', 2) for opt_n in opts if ':' in opt_n
        )
        options.append(option)

    if options:
        param['options'] = options

    hide = node.findtext('hide')
    if hide:
        param['hide'] = converter.to_python(hide.strip())

    return param


def convert_port_xml(node, converter):
    port = OrderedDict()
    port['name'] = node.findtext('name')

    dtype = converter.to_python(node.findtext('type'))
    # TODO: detect dyn message ports
    # todo: parse hide, tab tags
    port['domain'] = 'message' if dtype == 'message' else 'stream'
    if dtype == 'message':
        port['key'] = port['name']
    else:
        port['dtype'] = dtype
        vlen = node.findtext('vlen')
        if vlen:
            port['vlen'] = converter.to_python(vlen)

    return port
