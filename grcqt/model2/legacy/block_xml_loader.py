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
from itertools import imap


from lxml import etree
from mako.template import Template

from . block_category_loader import xml_to_nested_data
from .. import exceptions
from .. blocks import Block


BLOCK_DTD = etree.DTD(path.join(path.dirname(__file__), 'block.dtd'))

# match $abc123_a3, $[abc123.a3], $(abc123_a3), ${abc123_a3}
cheetah_substitution = re.compile(
    '\$\*?'
    '((?P<d1>\()|(?P<d2>\{)|(?P<d3>\[)|)'
    '(?P<arg>[_a-z][_a-z0-9]*(?:\.[_a-z][_a-z0-9]*)?)'
    '(?(d1)\)|(?(d2)\}|(?(d3)\]|)))'
)


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
    print class_definition
    return namespace[key]


BLOCK_TEMPLATE = Template('''\
<%!
def to_func_args(kwargs, newline=False):
    return (", \\n" if newline else ", ").join(
        "{}={}".format(key, repr(value))
        for key, value in kwargs.iteritems()
    )
%>
<%def name="on_update(on_update_kwargs)">\\
% if on_update_kwargs:
.on_update(
            ${ indent(to_func_args(on_update_kwargs, True), 3) }
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


class Raw(str):
    """a String without quotes in repr(...)"""
    def __repr__(self):
        return self


class Resolver(object):

    def __init__(self, n, params=None):
        self.n = n
        self.params = params or self.get_param_defaults(n)
        self.collected_on_update_kwargs = {}

    @staticmethod
    def get_param_defaults(block_n):
        params = {}
        for param_n in block_n.get('param', []):
            key = param_n.get('key')[0]
            value = param_n.get('value', [None])[0]
            if value is None:
                options_n = param_n.get('option', [])
                if options_n:
                    value = options_n[0].get('key', [None])[0]
            params[key] = value
        return params

    def pop_on_update_kwargs(self):
        on_update_kwargs = self.collected_on_update_kwargs
        self.collected_on_update_kwargs = {}
        return on_update_kwargs

    def _eval(self, key, expr):
        """Convert Cheetah generated python to on_update callbacks"""
        if expr.startswith('$'):  # template
            try:
                param_key = expr[1:]
                default = self.params[param_key] # simple subst
                self.collected_on_update_kwargs[key] = param_key
                return default
            except KeyError:
                pass

        if '$' in expr:
            used_params = []
            def convert(match):
                arg = match.group('arg')
                used_params.append(arg)
                return arg
            eval_str = cheetah_substitution.sub(convert, expr)
            print(expr, eval_str)
            value = eval(eval_str, self.params)
            self.collected_on_update_kwargs[key] = Raw(
                "lambda {}, **p: ({})".format(', '.join(used_params), eval_str)
            )
            return value
        return expr

    def eval(self, key, target_key=None):
        expr = self.get(key)
        return self._eval(target_key or key, expr) if expr else expr

    def get(self, *keys):
        """Get one or more string values for the specified keys"""
        items = [item if isinstance(item, str) else item[0]
                 for item in imap(lambda k: self.n.get(k, [None]), keys)]
        return items if len(keys) > 1 else items[0]

    def get_all(self, key):
        """Get a list of value for a key"""
        items = self.n.get(key, [])
        return items if not isinstance(items, str) else [items]

    def iter_sub_n(self, key):
        """Yield every item for key as (sub-)Resolver"""
        for n in self.get_all(key):
            yield self.__class__(n, self.params)



def get_param_options(param_n):
    options = []
    for option_n in param_n.iter_sub_n('option'):
        kwargs = OrderedDict()
        kwargs['name'], kwargs['value'] = option_n.get('name', 'key')
        kwargs.update(dict(
            opt_n.split(':', 2)
            for opt_n in option_n.get_all('opt')
            if ':' in opt_n and not opt_n.startswith(tuple(kwargs.keys()))
        ))
        options.append(kwargs)
    return options


def get_params(block_n):
    params = []
    for param_n in block_n.iter_sub_n('param'):
        kwargs = OrderedDict()
        kwargs['name'], kwargs['key'] = param_n.get('name', 'key')

        vtype = param_n.eval('type', 'vtype')
        kwargs['vtype'] = vtype if vtype != 'enum' else None

        #todo: parse hide tag
        value = param_n.get('value')
        if value:
            kwargs['default'] = value

        category = param_n.get('tab')
        if category:
            kwargs['category'] = category

        if vtype == 'enum':
            kwargs['cls'] = 'OptionsParam'
            kwargs['options'] = get_param_options(param_n)

        params.append((kwargs, param_n.pop_on_update_kwargs()))
    return params


def get_ports(block_n, direction):
    ports = []
    for port_n in block_n.iter_sub_n(direction):
        kwargs = OrderedDict()
        kwargs['name'] = port_n.get('name')

        dtype = port_n.eval('type', target_key='dtype')
        if dtype == 'message':
            method_name = "add_message_" + direction
            kwargs['key'] = kwargs['name']
        else:
            method_name = "add_stream_" + direction
            kwargs['dtype'] = dtype
            vlen = port_n.eval('vlen')
            if vlen:
                kwargs['vlen'] = int(vlen)

        ports.append((method_name, kwargs, port_n.pop_on_update_kwargs()))
    return ports


def convert_cheetah_template(expr):
    """converts a basic Cheetah expr to python string formatting"""
    markers = ('__!!start!!__', '__!!end!!__')
    # replace and tag substitutions (only tag, because ${key} is valid Cheetah)
    expr = cheetah_substitution.sub('{}\g<arg>{}'.format(*markers), expr
    )
    # mask all curly braces (those left are not no substitutions)
    expr = expr.replace("{", "{{").replace("}", "}}")
    # finally, replace markers with curly braces
    expr = expr.replace(markers[0], "{").replace(markers[1], "}")

    if any(kw in expr for kw in ("#set", "#end", "$")):
        raise exceptions.CheetahConversionException("Can't convert this expr")

    return expr


def get_make(block_n):
    var_make = block_n.get('var_make') or ''
    make = block_n.get('make')
    if make:
        make = "self.{key} = {key} = " + make

    make = ("\n" if var_make and make else "").join((var_make, make))

    try:
        make_format = convert_cheetah_template(make)
        if "\n" in make_format:
            make_template = '"""\n        {}\n    """'.format(
                indent(make_format, 2))
        else:
            make_template = repr(make_format)

    except exceptions.CheetahConversionException:

        make_template = 'lambda **params: CheetahTemplate(' \
                        '"""\n        {}\n    """, params)'.format(indent(make, 2))

    return make_template


def get_callbacks(blocks_n):
    callbacks = blocks_n.get_all('callback')
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
    block_n = Resolver(nested_data)

    key = block_n.get('key')

    return key, BLOCK_TEMPLATE.render(
        cls=key,
        base="Block",
        doc=block_n.get('doc'),

        name=block_n.get('name'),
        categories=block_n.get_all('category'),
        throttling=block_n.get('throttle'),

        make_template=get_make(block_n),
        imports=block_n.get_all('import'),
        callbacks=get_callbacks(block_n),

        params=get_params(block_n),
        sinks=get_ports(block_n, 'sink'),
        sources=get_ports(block_n, 'source'),

        # helper functions
        indent=indent
    )
