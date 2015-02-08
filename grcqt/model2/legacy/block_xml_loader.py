# Copyright 2014 Free Software Foundation, Inc.
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

from lxml import etree
from mako.template import Template

from .. blocks import Block


class CheetahConversionException(Exception):
    pass


BLOCK_DTD = etree.DTD(path.join(path.dirname(__file__), 'block.dtd'))

# match $abc123_a3, $[abc123.a3], $(abc123_a3), ${abc123_a3}
cheetah_substitution = re.compile(
    r'\$\*?'
    r'((?P<d1>\()|(?P<d2>\{)|(?P<d3>\[)|)'
    r'(?P<arg>[_a-zA-Z][_a-zA-Z0-9]*(?:\.[_a-zA-Z][_a-zA-Z0-9]*)?)'
    r'(?(d1)\)|(?(d2)\}|(?(d3)\]|)))'
    r'(?<!\.)'
)

reserved_block_keys = ('import', )  # todo: add more keys


def load_block_xml(xml_file):
    """Load block description from xml file"""
    try:
        xml = etree.parse(xml_file).getroot()
        BLOCK_DTD.validate(xml)
    except etree.LxmlError:
        return

    key, class_definition = construct_block_class(xml)
    namespace = dict(__name__="__grc__", Block=Block)
    try:
        exec class_definition in namespace
    except SyntaxError as e:
        raise SyntaxError(repr(e) + ':\n' + class_definition)
    # print class_definition
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
    label = ${ repr(label) }
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


class OptionsString(str):
    """a string with custom attributes (for opt values)"""
    def __new__(cls, string, extra=None):
        """overriding new to get the extra argument"""
        ob = super(OptionsString, cls).__new__(cls, string)
        return ob

    def __init__(self, string, extra=None):
        """set all key/values in dict extra ass instance attributes"""
        super(OptionsString, self).__init__(string)
        for key, value in (extra or {}).iteritems():
            setattr(self, key, value)


class Resolver(object):

    def __init__(self, xml, params=None):
        self.xml = xml
        self.params = params or self.get_param_defaults(xml)
        self.collected_on_update_kwargs = {}

    @staticmethod
    def get_param_defaults(block_e):
        params = {}
        for param_e in block_e.getiterator('param'):
            key = param_e.findtext('key')
            value = param_e.findtext('value') or ''
            options_e = param_e.findall('option')
            if options_e:
                value = OptionsString(
                    string=options_e[0].findtext('key'),
                    extra=dict(opt_e.text.split(':', 2)
                               for opt_e in options_e[0].findall('opt')))
            params[key] = value
        return params

    def pop_on_update_kwargs(self):
        on_update_kwargs = self.collected_on_update_kwargs
        self.collected_on_update_kwargs = {}
        return on_update_kwargs

    def _eval(self, key, expr):
        """Convert Cheetah generated python to on_update callbacks"""
        if not expr or '$' not in expr:  # skip empty and text-only expressions
            return expr, False

        if expr.startswith('$'):  # simple subst
            try:
                param_key = expr[1:]
                evaluated = self.params[param_key]  # raises KeyError
                self.collected_on_update_kwargs[key] = param_key
                return evaluated, True
            except KeyError:
                pass  # no param for this key. Go to full mode

        params_used = []

        def convert(match):
            arg = match.group('arg')
            params_used.append(arg.split('.')[0])
            return arg
        eval_str = cheetah_substitution.sub(convert, expr)

        self.collected_on_update_kwargs[key] = Raw(
            "lambda {}, **p: ({})".format(', '.join(params_used), eval_str)
        )
        try:
            return eval(eval_str, self.params), True
        except:
            return None, True

    def evaltext(self, key, target_key=None):
        expr = self.findtext(key)
        return self._eval(target_key or key, expr)

    def findtext(self, *keys):
        """Get one or more string values for the specified keys"""
        items = [self.xml.findtext(key) for key in keys]
        return items if len(keys) > 1 else items[0]

    def findtext_all(self, key):
        """Get a list of values for a key"""
        return [elem.text for elem in self.xml.getiterator(key)]

    def getiterator(self, key):
        """Yield every item for key as (sub-)Resolver"""
        for xml in self.xml.getiterator(key):
            yield self.__class__(xml, self.params)


def get_param_options(param_e):
    options = []
    for option_n in param_e.getiterator('option'):
        kwargs = OrderedDict()
        kwargs['label'], kwargs['value'] = option_n.findtext('name', 'key')
        kwargs.update(dict(
            opt_n.split(':', 2)
            for opt_n in option_n.findtext_all('opt')
            if ':' in opt_n and not opt_n.startswith(tuple(kwargs.keys()))
        ))
        options.append(kwargs)
    return options


def get_params(block_e):
    params = []
    for param_e in block_e.getiterator('param'):
        kwargs = OrderedDict()
        kwargs['label'], kwargs['uid'] = param_e.findtext('label', 'key')

        vtype, gets_updated = param_e.evaltext('type', 'vtype')
        if not gets_updated:
            kwargs['vtype'] = vtype if vtype != 'enum' else None

        # todo: parse hide tag
        value = param_e.findtext('value')
        if value:
            kwargs['default'] = value

        category = param_e.findtext('tab')
        if category:
            kwargs['category'] = category

        if vtype == 'enum':
            kwargs['cls'] = 'OptionsParam'
            kwargs['options'] = get_param_options(param_e)

        params.append((kwargs, param_e.pop_on_update_kwargs()))
    return params


def get_ports(block_e, direction):
    ports = []
    for port_e in block_e.getiterator(direction):
        kwargs = OrderedDict()
        kwargs['name'] = port_e.findtext('name')

        dtype, dtype_gets_updated = port_e.evaltext('type', target_key='dtype')
        if dtype == 'message':
            method_name = "add_message_" + direction
            kwargs['key'] = kwargs['name']
        else:
            method_name = "add_stream_" + direction
            if not dtype_gets_updated:
                kwargs['dtype'] = dtype
            vlen, vlen_gets_updated = port_e.evaltext('vlen')
            if not vlen_gets_updated and vlen:
                kwargs['vlen'] = vlen

        ports.append((method_name, kwargs, port_e.pop_on_update_kwargs()))
    return ports


def convert_cheetah_template(expr):
    """converts a basic Cheetah expr to python string formatting"""
    markers = ('__!!start!!__', '__!!end!!__')
    # replace and tag substitutions (only tag, because ${key} is valid Cheetah)
    expr = cheetah_substitution.sub('{}\g<arg>{}'.format(*markers), expr)
    # mask all curly braces (those left are not no substitutions)
    expr = expr.replace("{", "{{").replace("}", "}}")
    # finally, replace markers with curly braces
    expr = expr.replace(markers[0], "{").replace(markers[1], "}")

    if any(kw in expr for kw in ("#set", "#end", "$")):
        raise CheetahConversionException("Can't convert this expr")

    return expr


def get_make(block_e):
    var_make = block_e.findtext('var_make') or ''
    make = block_e.findtext('make')
    if make:
        make = "self.$key = $key = " + make

    make = ("\n" if var_make and make else "").join((var_make, make))

    try:
        make_format = convert_cheetah_template(make)
        if "\n" in make_format:
            make_template = '"""\n        {}\n    """'.format(
                indent(make_format, 2))
        else:
            make_template = repr(make_format)

    except CheetahConversionException:

        make_template = ('lambda **params: CheetahTemplate("""\n'
                         '        {}\n'
                         '    """, params)').format(indent(make, 2))

    return make_template


def get_callbacks(blocks_e):
    callbacks = blocks_e.findtext_all('callback')
    for i in xrange(len(callbacks)):
        try:
            callbacks[i] = convert_cheetah_template(callbacks[i])
        except CheetahConversionException:
            callbacks[i] = 'lambda **params: CheetahTemplate({!r}, params)' \
                           ''.format(callbacks[i])
    return callbacks


def indent(s, level=1):
    if isinstance(s, str):
        s = s.strip().split('\n')
        ind = s[0].index(s[0].strip())
        s = [line[ind:] for line in s]
    return ("\n" + " " * 4 * level).join(s)


def construct_block_class(xml):
    block_e = Resolver(xml)

    key = block_e.findtext('key')
    if key in reserved_block_keys:
        key += '_'

    return key, BLOCK_TEMPLATE.render(
        cls=key,
        base="Block",
        doc=block_e.findtext('doc'),

        label=block_e.findtext('name'),
        categories=block_e.findtext_all('category'),
        throttling=block_e.findtext('throttle'),

        make_template=get_make(block_e),
        imports=block_e.findtext_all('import'),
        callbacks=get_callbacks(block_e),

        params=get_params(block_e),
        sinks=get_ports(block_e, 'sink'),
        sources=get_ports(block_e, 'source'),

        # helper functions
        indent=indent
    )
