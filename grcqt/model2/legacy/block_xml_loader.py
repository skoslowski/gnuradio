"""
Copyright 2014 Free Software Foundation, Inc.
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

from os import path
from collections import OrderedDict
import re

from lxml import etree
from mako.template import Template

from . block_category_loader import xml_to_nested_data
from .. import exceptions
from .. blocks import Block


BLOCK_DTD = etree.DTD(path.join(path.dirname(__file__), 'block.dtd'))


def load_block_xml(xml_file):
    """Load block description from xml file"""
    try:
        xml = etree.parse(xml_file).getroot()
        BLOCK_DTD.validate(xml)
    except etree.LxmlError:
        return

    n = xml_to_nested_data(xml)[1]
    n['block_wrapper_path'] = xml_file  # inject block wrapper path

    key, class_definition = construct_block_class_from_nested_data(n)
    namespace = dict(__name__="__grc__", Block=Block)
    try:
        exec class_definition in namespace
    except SyntaxError as e:
        raise SyntaxError(e.message + ':\n' + class_definition)

    return namespace[key]

BLOCK_TEMPLATE = Template('''\
<%!
def to_func_args(kwargs):
    return ", ".join(
        "{}={}".format(key, repr(value))
        for key, value in kwargs.iteritems()
    )
%>
<%def name="on_update(on_update_kwargs)">\\
% if updates:
.on_update(
            ${ to_func_args(on_update_kwargs) }
        )\\
% endif
</%def>
class ${ cls }(Block):
    % if doc:
    """
    ${ indent(doc) }
    """
    % endif
    name = ${ repr(name) }
    % if categories:
    categories = ${ repr(categories) }
    % endif
    % if throttling:
    throttling = True
    % endif
    % if imports:

    % if len(imports) > 1:
    import_template = """
        ${ indent(imports, 2) }
    """
    % else:
    import_template = ${ repr(imports[0]) }
    % endif
    % endif
    % if make_template:

    make_template = ${ make_template }
    % endif
    % if callbacks:

    callbacks = ${ repr(callbacks) }
    % endif

    def setup(self, **kwargs):
        super(XMLBlock, self).setup(**kwargs)

        # params
        % for kwargs, on_update_kwargs in params:
        % if 'options' in kwargs:
        <%
            options = kwargs.pop('options')
        %>p = self.add_param(${ to_func_args(kwargs) })${ on_update(on_update_kwargs) }
        % for option in options:
        p.add_option(${ to_func_args(option) })
        % endfor
        % else:
        self.add_param(${ to_func_args(kwargs) })${ on_update(on_update_kwargs) }
        % endif
        % endfor
        % if sinks:

        # sinks
        % for method, kwargs, on_update_kwargs in sinks:
        self.${ method }(${ to_func_args(kwargs) })${ on_update(on_update_kwargs) }
        % endfor
        % endif
        % if sources:

        # sources
        % for method, kwargs, on_update_kwargs in sources:
        self.${ method }(${ to_func_args(kwargs) })${ on_update(on_update_kwargs) }
        % endfor
        % endif
''')


class Resolver(object):

    def __init__(self, block_n):
        self.params = dict()
        self.collected_on_update_kwargs = {}
        self.get_param_defaults(block_n)

    def get_param_defaults(self, block_n):
        for param_n in block_n.get('param', []):
            key = self.get_raw(param_n, 'key')
            value = self.get_raw(param_n, 'value')
            if value is None:
                options = param_n.get('option')
                if options:
                    value = self.get_raw(options[0], 'key')
            self.params[key] = value


    def pop_on_update_kwargs(self):
        on_update_kwargs = self.collected_on_update_kwargs
        self.collected_on_update_kwargs = {}
        return on_update_kwargs

    def eval(self, key, expr):
        if '$' in expr:  # template
            try:
                param_key = expr[1:]
                default = self.params[param_key] # simple subst
                self.collected_on_update_kwargs[key] = param_key
                return default
            except KeyError:
                pass
            # todo parse/eval advanced template
        return expr

    def get(self, namespace, key, key2=None):
        expr = self.get_raw(namespace, key)
        return self.eval(key2 or key, expr) if expr else expr

    @staticmethod
    def get_raw(namespace, key):
        items = namespace.get(key, [None])
        if not isinstance(items, str):
            items = items[0]
        return items


def get_param_options(param_n, resolver):
    options = []
    for option_n in param_n.get('option', []):
        kwargs = OrderedDict()
        kwargs['name'] = resolver.get_raw(option_n, 'name')
        kwargs['value'] = resolver.get_raw(option_n, 'key')
        kwargs.update(dict(
            opt_n.split(':', 2)
            for opt_n in option_n.get('opt', [])
            if ':' in opt_n and not opt_n.startswith(tuple(kwargs.keys()))
        ))
        options.append(kwargs)
    return options


def get_params(block_n, resolver):
    params = []
    for n in block_n.get('param', []):
        kwargs = OrderedDict()
        kwargs['name'] = resolver.get_raw(n, 'name')
        kwargs['key'] = resolver.get_raw(n, 'key')

        vtype = resolver.get(n, 'type')
        kwargs['vtype'] = vtype if vtype != 'enum' else None

        #todo: parse hide tag
        value = resolver.get_raw(n, 'value')
        if value:
            kwargs['default'] = value

        category = resolver.get_raw(n, 'tab')
        if category:
            kwargs['category'] = category

        if vtype == 'enum':
            kwargs['cls'] = 'OptionsParam'
            kwargs['options'] = get_param_options(n, resolver)

        params.append((kwargs, resolver.pop_on_update_kwargs()))
    return params


def get_ports(block_n, resolver, direction):
    ports = []
    for n in block_n.get(direction, []):
        kwargs = OrderedDict()
        kwargs['name'] = resolver.get_raw(n, 'name')

        dtype = resolver.get(n, 'type', 'dtype')
        if dtype == 'message':
            method_name = "add_message_" + direction
            kwargs['key'] = kwargs['name']
        else:
            method_name = "add_stream_" + direction
            kwargs['dtype'] = dtype
            vlen = resolver.get(n, 'vlen')
            if vlen:
                kwargs['vlen'] = int(vlen)

        ports.append((method_name, kwargs, resolver.pop_on_update_kwargs()))
    return ports


def convert_cheetah_template(expr):
    """converts a basic Cheetah expr to python string formatting"""
    markers = ('__!!start!!__', '__!!end!!__')
    # match $abc123_a3, $[abc123.a3], $(abc123_a3), ${abc123_a3}
    cheetah_subst = re.compile(
        '\$\*?' \
        '((?P<d1>\()|(?P<d2>\{)|(?P<d3>\[)|)' \
        '(?P<arg>[_a-z][_a-z0-9]*)(?P<subarg>(\.[_a-z][_a-z0-9]*)?)' \
        '(?(d1)\)|(?(d2)\}|(?(d3)\]|)))'
    )
    # replace and tag substitutions (only tag, because ${key} is valid Cheetah)
    expr = cheetah_subst.sub(
        lambda match: '{m[0]}{arg}{i}{m[1]}'.format(
            m=markers,
            arg=match.group('arg'),
            i="[{!r}]".format(match.group('subarg')[1:]) if match.group("subarg") else ""
        ), expr
    )
    # mask all curly braces (those left are not no substitutions)
    expr = expr.replace("{", "{{").replace("}", "}}")
    # finally, replace markers with curly braces
    expr = expr.replace(markers[0], "{").replace(markers[1], "}")

    if any(kw in expr for kw in ("#set", "#end", "$")):
        raise exceptions.CheetahConversionException("Can't convert this expr")

    return expr


def get_make(block_n, resolver):
    key = block_n['key'][0]
    var_make = block_n.get('var_make', [''])[0]
    make = block_n['make'][0]
    if make:
        make = "self.{0} = {0} = {1}".format(key, make)

    make = ("\n" if var_make and make else "").join((var_make, make))

    try:
        make_format = convert_cheetah_template(make)
        if "\n" in make_format:
            make_template = '"""\n        {}\n    """'.format(
                indent(make_format, 2))
        else:
            make_template = repr(make_format)

    except exceptions.CheetahConversionException:
        make_template = 'lambda params: CheetahTemplate(' \
                        '"""\n        {}\n    """, params)'.format(indent(make, 2))

    return make_template


def get_callbacks(blocks_n, resolver):
    callbacks = blocks_n.get('callback', [])
    for i in xrange(len(callbacks)):
        try:
            callbacks[i] = convert_cheetah_template(callbacks[i])

        except exceptions.CheetahConversionException:
            callbacks[i] = 'lambda params: CheetahTemplate({!r}, params)'.format(callbacks[i])
    return callbacks

def indent(s, level=1):
    if isinstance(s, str):
        s = s.strip().split('\n')
        ind = s[0].index(s[0].strip())
        s = [line[ind:] for line in s]
    return ("\n" + " " * 4 * level).join(s)


def to_camel_case(key):
    return re.sub("(^([a-z])|_([a-z])?)", lambda m:
        (m.group(2) or m.group(3) or "").upper(), key)


def construct_block_class_from_nested_data(nested_data):
    n = nested_data
    r = Resolver(n)

    key = r.get_raw(n, 'key')

    return key, BLOCK_TEMPLATE.render(
        cls=key,
        base="Block",
        doc=r.get_raw(n, 'doc'),

        name=r.get_raw(n, 'name'),
        categories=n.get('category', []),
        throttling=r.get_raw(n, 'throttle'),

        make_template=get_make(n, r),
        imports=n.get('import', []),
        callbacks=get_callbacks(n, r),

        params=get_params(n, r),
        sinks=get_ports(n, r, 'sink'),
        sources=get_ports(n, r, 'source'),

        # helper functions
        indent=indent
    )
