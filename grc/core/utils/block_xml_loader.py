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
from os import path
from collections import OrderedDict
import re
import functools

import six
import yaml
from lxml import etree


##############################################################################
# YAML Stuff
##############################################################################


class Eval(unicode):
    """String subtype explicitly enable evaluation of the provided expression"""
    tag = u'eval'


class Mako(unicode):
    """String subtype explicitly enable evaluation of the provided expression"""
    tag = u'mako'


class OrderedDictFlowing(OrderedDict):
    pass


def yaml_constructor(data_type):
    def decorator(func):
        yaml.add_constructor(data_type.tag, func)
        return func
    return decorator


def yaml_representer(data_type):
    def decorator(func):
        yaml.add_representer(data_type, func)
        return func
    return decorator


@yaml_constructor(Eval)
def construct_code_string(loader, node):
    return Eval(loader.construct_scalar(node))


@yaml_representer(Eval)
def represent_code_string(representer, data):
    node = representer.represent_scalar(tag=Eval.tag, value=data)
    if "'" in data and '"' not in data:
        node.style = '"'
    return node


@yaml_representer(Mako)
def represent_code_string(representer, data):
    return representer.represent_scalar(tag=Mako.tag, value=data)


@yaml_representer(OrderedDict)
def represent_ordered_mapping(representer, data):
    self = representer

    value = []
    node = yaml.MappingNode(u'tag:yaml.org,2002:map', value, flow_style=False)

    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node

    for item_key, item_value in six.iteritems(data):
        node_key = self.represent_data(item_key)
        node_value = self.represent_data(item_value)
        value.append((node_key, node_value))

    return node


@yaml_representer(OrderedDictFlowing)
def represent_ordered_mapping_flowing(representer, data):
    node = represent_ordered_mapping(representer, data)
    node.flow_style = True
    return node


@yaml_representer(yaml.nodes.ScalarNode)
def represent_node(representer, node):
    return node

scalar_node = functools.partial(yaml.ScalarNode, u'tag:yaml.org,2002:str')


##############################################################################
# Cheetah Stuff
##############################################################################


class CheetahConversionException(Exception):
    pass


# match $abc123_a3, $[abc123.a3], $(abc123_a3), ${abc123_a3}
cheetah_substitution = re.compile(
    r'\$\*?'
    r'((?P<d1>\()|(?P<d2>\{)|(?P<d3>\[)|)'
    r'(?P<arg>[_a-zA-Z][_a-zA-Z0-9]*(?:\.[_a-zA-Z][_a-zA-Z0-9]*)?(?:\(\))?)'
    r'(?(d1)\)|(?(d2)\}|(?(d3)\]|)))'
    r'(?<!\.)'
)

cheetah_inline_if = re.compile(r'#if (?P<cond>.*) then (?P<then>.*) else (?P<else>.*) ?(#|$)')

cheetah_set = re.compile(r'^\w*#set (?P<set>.*)\w*($|#.*)')


def convert_cheetah_to_format_string(expr):
    """converts a basic Cheetah expr to python string formatting"""
    markers = ('__!!start!!__', '__!!end!!__')
    # replace and tag substitutions (only tag, because ${key} is valid Cheetah)
    expr = cheetah_substitution.sub('{}\g<arg>{}'.format(*markers), expr)
    # mask all curly braces (those left are not no substitutions)
    expr = expr.replace("{", "{{").replace("}", "}}")
    # finally, replace markers with curly braces
    expr = expr.replace(markers[0], "{").replace(markers[1], "}")

    if any(kw in expr for kw in ("#set", "#end", "$")):
        raise CheetahConversionException("Can't convert this expr", expr)

    return expr


def convert_cheetah_to_mako(expr):
    """converts a basic Cheetah expr to python string formatting"""
    output = []

    def convert_set_directive(match):
        arg = match.group('set')
        arg = cheetah_substitution.sub('\g<arg>', arg)
        return '<% {} %>'.format(arg)

    for line in expr.strip().splitlines():
        line = cheetah_set.sub(convert_set_directive, line)
        line = cheetah_substitution.sub('${ \g<arg> }', line)
        output.append(line)
    return Mako('\n'.join(output))


def convert_cheetah_to_python(expr):
    """converts a basic Cheetah expr to python string formatting"""
    expr = str(expr)
    if '$' not in expr:
        return expr
    expr = cheetah_substitution.sub('\g<arg>', expr)

    expr = cheetah_inline_if.sub(r'(\g<then> if \g<cond> else \g<else>)', expr)

    if any(kw in expr for kw in ("#set", "#end", "$")):
        raise CheetahConversionException("Can't convert this expr", expr)

    return Eval(expr)


##############################################################################
# XML Stuff
##############################################################################

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
    out = yaml.dump(data, default_flow_style=False, indent=4)

    replace = [
        ('!<eval>', '!eval'),
        ('!<mako>', '!mako'),
        ('params:', '\nparams:'),
        ('ports:', '\nports:'),
        ('import:', '\nimport:'),
        ('documentation:', '\ndocumentation:'),
    ]
    for r in replace:
        out = out.replace(*r)

    print()
    print()
    print(out)


def convert_block_xml(node):
    key = node.findtext('key')
    if key in reserved_block_keys:
        key += '_'

    data = OrderedDict()
    data['key'] = key
    data['name'] = node.findtext('name')
    data['category'] = node.findtext('category')

    data['params'] = params = []
    for param_node in node.getiterator('param'):
        params.append(convert_param_xml(param_node))

    data['ports'] = ports = []
    for direction in ('sink', 'source'):
        for port_node in node.getiterator(direction):
            ports.append(convert_port_xml(port_node, direction))

    imports = []
    for import_node in node.getiterator('import'):
        imports.append(convert_cheetah_to_format_string(import_node.text))
    if imports:
        data['import'] = imports if len(imports) > 1 else imports[0]

    make = node.findtext('make')
    if '\n' in make:
        make = convert_cheetah_to_mako(make)
        data['make'] = scalar_node(make, style='|' if '\n' in make else None)
    else:
        data['make'] = convert_cheetah_to_format_string(make)

    data['callbacks'] = []

    docs = node.findtext('doc')
    if docs:
        docs = docs.strip().replace('\\\n', '').replace('\n\n', '\n')
        data['documentation'] = scalar_node(docs, style='>')

    return data


def convert_param_xml(node):
    param = OrderedDict()
    param['name'] = node.findtext('key')
    param['label'] = node.findtext('name').strip()
    param['type'] = convert_cheetah_to_python(node.findtext('type'))

    value = node.findtext('value')
    if value:
        param['default'] = value

    # todo: parse hide, tab tags

    options = []
    for option_n in node.getiterator('option'):
        option = OrderedDict()
        option['label'] = option_n.findtext('name')
        option['value'] = option_n.findtext('key')

        opts = (opt.text for opt in option_n.getiterator('opt'))
        option['extra'] = OrderedDictFlowing(
            opt_n.split(':', 2) for opt_n in opts if ':' in opt_n
        )
        options.append(option)

    if options:
        param['options'] = options

    hide = node.findtext('hide')
    if hide:
        param['hide'] = convert_cheetah_to_python(hide.strip())

    return param


def convert_port_xml(node, direction):
    port = OrderedDict()
    port['label'] = node.findtext('name')

    dtype = convert_cheetah_to_python(node.findtext('type'))
    # TODO: detect dyn message ports
    # todo: parse hide, tab tags
    port['domain'] = 'message' if dtype == 'message' else 'stream'
    port['direction'] = direction
    if dtype == 'message':
        port['key'] = port['label']
    else:
        port['dtype'] = dtype
        vlen = node.findtext('vlen')
        if vlen:
            port['vlen'] = convert_cheetah_to_python(vlen)

    return port
