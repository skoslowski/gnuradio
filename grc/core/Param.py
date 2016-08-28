"""
Copyright 2008-2015 Free Software Foundation, Inc.
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

from __future__ import absolute_import

import ast
import re
import collections

from six.moves import builtins, filter, map, range, zip

from . import Constants
from .Element import Element, nop_write, EvaluatedEnum, Evaluated

# Blacklist certain ids, its not complete, but should help
ID_BLACKLIST = ['self', 'options', 'gr', 'blks2', 'math', 'firdes'] + dir(builtins)
try:
    from gnuradio import gr
    ID_BLACKLIST.extend(attr for attr in dir(gr.top_block()) if not attr.startswith('_'))
except ImportError:
    pass

_check_id_matcher = re.compile('^[a-z|A-Z]\w*$')
_show_id_matcher = re.compile('^(variable\w*|parameter|options|notebook)$')


class TemplateArg(object):
    """
    A cheetah template argument created from a param.
    The str of this class evaluates to the param's to code method.
    The use of this class as a dictionary (enum only) will reveal the enum opts.
    The __call__ or () method can return the param evaluated to a raw python data type.
    """

    def __init__(self, param):
        self._param = param

    def __getitem__(self, item):
        param = self._param
        attributes = param.options.attributes[param.get_value()]
        return str(attributes.get(item)) or NotImplemented

    def __str__(self):
        return str(self._param.to_code())

    def __call__(self):
        return self._param.get_evaluated()


class Param(Element):

    is_param = True

    name = Evaluated(str, default='no name', name='name')
    dtype = EvaluatedEnum(Constants.PARAM_TYPE_NAMES, default='raw', name='dtype')
    # hidden = Evaluated((bool, int), default=False, name='hidden')

    def __init__(self, parent, key, label='', dtype='raw', default='',
                 options=None, category='', hide='none', **kwargs):
        """Make a new param from nested data"""
        super(Param, self).__init__(parent)
        self.key = key
        self.name = label.strip() or key.title()
        self.category = category or Constants.DEFAULT_PARAM_TAB

        self.dtype = dtype
        self.value = self.default = default

        self.options = self._init_options(options or [])

        self.hide = hide or 'none'
        # end of args ########################################################

        self._evaluated = None
        self._init = False
        self._hostage_cells = list()
        self.template_arg = TemplateArg(self)

    def _init_options(self, options_n):
        """Create the Option objects from the n data"""
        options = collections.OrderedDict()
        options.attributes = collections.defaultdict(dict)

        for option_n in options_n:
            value, name = option_n['value'], str(option_n['name'])
            # Test against repeated keys
            if value in options:
                raise KeyError('Value "{}" already exists in options'.format(value))
            # Store the option
            options[value] = name
            options.attributes[value] = option_n.get('attributes', {})

        default = next(iter(options)) if options else ''
        if not self.value:
            self.value = self.default = default

        if self.is_enum() and self.value not in options:
            self.value = self.default = default  # TODO: warn
            # raise ValueError('The value {!r} is not in the possible values of {}.'
            #                  ''.format(self.get_value(), ', '.join(self.options)))
        return options

    def __str__(self):
        return 'Param - {}({})'.format(self.name, self.key)

    def __repr__(self):
        return '{!r}.param[{}]'.format(self.parent, self.key)

    @EvaluatedEnum('none all part')
    def hide(self):
        """
        Get the hide value from the base class.
        Hide the ID parameter for most blocks. Exceptions below.
        If the parameter controls a port type, vlen, or nports, return part.
        If the parameter is an empty grid position, return part.
        These parameters are redundant to display in the flow graph view.

        Returns:
            hide the hide property string
        """
        block = self.parent_block

        hide = EvaluatedEnum.default_eval_func(Param.hide, self)
        if hide != 'none':
            return hide

        # Hide ID in non variable blocks
        if self.key == 'id' and not _show_id_matcher.match(block.key):
            return 'part'
        # Hide port controllers for type and nports
        if self.key in ' '.join(p.get_raw('dtype') + ' ' + str(p.get_raw('multiplicity')) for p in self.parent.get_ports()):
            return 'part'
        # Hide port controllers for vlen, when == 1
        if self.key in ' '.join(str(p.get_raw('vlen')) for p in self.parent.get_ports()):
            try:
                if int(self.get_evaluated()) == 1:
                    return 'part'
            except:
                pass
        return hide

    def rewrite(self):
        Element.rewrite(self)
        del self.name
        del self.dtype
        del self.hide

        self._evaluated = None
        try:
            self._evaluated = self.evaluate()
        except Exception as e:
            self.add_error_message(str(e))

    def validate(self):
        """
        Validate the param.
        The value must be evaluated and type must a possible type.
        """
        Element.validate(self)
        if self.dtype not in Constants.PARAM_TYPE_NAMES:
            self.add_error_message('Type "{}" is not a possible type.'.format(self.dtype))

    def get_evaluated(self):
        return self._evaluated

    def evaluate(self):
        """
        Evaluate the value.

        Returns:
            evaluated type
        """
        self._init = True
        self._lisitify_flag = False
        self._stringify_flag = False
        self._hostage_cells = list()
        t = self.dtype
        v = self.get_value()

        #########################
        # Enum Type
        #########################
        if self.is_enum():
            return v

        #########################
        # Numeric Types
        #########################
        elif t in ('raw', 'complex', 'real', 'float', 'int', 'hex', 'bool'):
            # Raise exception if python cannot evaluate this value
            try:
                e = self.parent_flowgraph.evaluate(v)
            except Exception as e:
                raise Exception('Value "{}" cannot be evaluated:\n{}'.format(v, e))
            # Raise an exception if the data is invalid
            if t == 'raw':
                return e
            elif t == 'complex':
                if not isinstance(e, Constants.COMPLEX_TYPES):
                    raise Exception('Expression "{}" is invalid for type complex.'.format(str(e)))
                return e
            elif t == 'real' or t == 'float':
                if not isinstance(e, Constants.REAL_TYPES):
                    raise Exception('Expression "{}" is invalid for type float.'.format(str(e)))
                return e
            elif t == 'int':
                if not isinstance(e, Constants.INT_TYPES):
                    raise Exception('Expression "{}" is invalid for type integer.'.format(str(e)))
                return e
            elif t == 'hex':
                return hex(e)
            elif t == 'bool':
                if not isinstance(e, bool):
                    raise Exception('Expression "{}" is invalid for type bool.'.format(str(e)))
                return e
            else:
                raise TypeError('Type "{}" not handled'.format(t))
        #########################
        # Numeric Vector Types
        #########################
        elif t in ('complex_vector', 'real_vector', 'float_vector', 'int_vector'):
            if not v:
                # Turn a blank string into an empty list, so it will eval
                v = '()'
            # Raise exception if python cannot evaluate this value
            try:
                e = self.parent.parent.evaluate(v)
            except Exception as e:
                raise Exception('Value "{}" cannot be evaluated:\n{}'.format(v, e))
            # Raise an exception if the data is invalid
            if t == 'complex_vector':
                if not isinstance(e, Constants.VECTOR_TYPES):
                    self._lisitify_flag = True
                    e = [e]
                if not all([isinstance(ei, Constants.COMPLEX_TYPES) for ei in e]):
                    raise Exception('Expression "{}" is invalid for type complex vector.'.format(str(e)))
                return e
            elif t == 'real_vector' or t == 'float_vector':
                if not isinstance(e, Constants.VECTOR_TYPES):
                    self._lisitify_flag = True
                    e = [e]
                if not all([isinstance(ei, Constants.REAL_TYPES) for ei in e]):
                    raise Exception('Expression "{}" is invalid for type float vector.'.format(str(e)))
                return e
            elif t == 'int_vector':
                if not isinstance(e, Constants.VECTOR_TYPES):
                    self._lisitify_flag = True
                    e = [e]
                if not all([isinstance(ei, Constants.INT_TYPES) for ei in e]):
                    raise Exception('Expression "{}" is invalid for type integer vector.'.format(str(e)))
                return e
        #########################
        # String Types
        #########################
        elif t in ('string', 'file_open', 'file_save', '_multiline', '_multiline_python_external'):
            # Do not check if file/directory exists, that is a runtime issue
            try:
                e = self.parent.parent.evaluate(v)
                if not isinstance(e, str):
                    raise Exception()
            except:
                self._stringify_flag = True
                e = str(v)
            if t == '_multiline_python_external':
                ast.parse(e)  # Raises SyntaxError
            return e
        #########################
        # Unique ID Type
        #########################
        elif t == 'id':
            # Can python use this as a variable?
            if not _check_id_matcher.match(v):
                raise Exception('ID "{}" must begin with a letter and may contain letters, numbers, and underscores.'.format(v))
            ids = [param.get_value() for param in self.get_all_params(t)]

            # Id should only appear once, or zero times if block is disabled
            if ids.count(v) > 1:
                raise Exception('ID "{}" is not unique.'.format(v))
            if v in ID_BLACKLIST:
                raise Exception('ID "{}" is blacklisted.'.format(v))
            return v

        #########################
        # Stream ID Type
        #########################
        elif t == 'stream_id':
            # Get a list of all stream ids used in the virtual sinks
            ids = [param.get_value() for param in filter(
                lambda p: p.parent.is_virtual_sink(),
                self.get_all_params(t),
            )]
            # Check that the virtual sink's stream id is unique
            if self.parent.is_virtual_sink():
                # Id should only appear once, or zero times if block is disabled
                if ids.count(v) > 1:
                    raise Exception('Stream ID "{}" is not unique.'.format(v))
            # Check that the virtual source's steam id is found
            if self.parent.is_virtual_source():
                if v not in ids:
                    raise Exception('Stream ID "{}" is not found.'.format(v))
            return v

        #########################
        # GUI Position/Hint
        #########################
        elif t == 'gui_hint':
            if ':' in v:
                tab, pos = v.split(':')
            elif '@' in v:
                tab, pos = v, ''
            else:
                tab, pos = '', v

            if '@' in tab:
                tab, index = tab.split('@')
            else:
                index = '?'

            # TODO: Problem with this code. Produces bad tabs
            widget_str = ({
                (True, True): 'self.%(tab)s_grid_layout_%(index)s.addWidget(%(widget)s, %(pos)s)',
                (True, False): 'self.%(tab)s_layout_%(index)s.addWidget(%(widget)s)',
                (False, True): 'self.top_grid_layout.addWidget(%(widget)s, %(pos)s)',
                (False, False): 'self.top_layout.addWidget(%(widget)s)',
            }[bool(tab), bool(pos)]) % {'tab': tab, 'index': index, 'widget': '%s', 'pos': pos}

            # FIXME: Move replace(...) into the make template of the qtgui blocks
            # Return a string here
            class GuiHint(object):
                def __init__(self, ws):
                    self._ws = ws

                def __call__(self, w):
                    return (self._ws.replace('addWidget', 'addLayout') if 'layout' in w else self._ws) % w

                def __str__(self):
                    return self._ws
            return GuiHint(widget_str)
        #########################
        # Import Type
        #########################
        elif t == 'import':
            # New namespace
            n = dict()
            try:
                exec(v, n)
            except ImportError:
                raise Exception('Import "{}" failed.'.format(v))
            except Exception:
                raise Exception('Bad import syntax: "{}".'.format(v))
            return [k for k in list(n.keys()) if str(k) != '__builtins__']

        #########################
        else:
            raise TypeError('Type "{}" not handled'.format(t))

    def to_code(self):
        """
        Convert the value to code.
        For string and list types, check the init flag, call evaluate().
        This ensures that evaluate() was called to set the xxxify_flags.

        Returns:
            a string representing the code
        """
        self._init = True
        v = self.get_value()
        t = self.dtype
        # String types
        if t in ('string', 'file_open', 'file_save', '_multiline', '_multiline_python_external'):
            if not self._init:
                self.evaluate()
            return repr(v) if self._stringify_flag else v

        # Vector types
        elif t in ('complex_vector', 'real_vector', 'float_vector', 'int_vector'):
            if not self._init:
                self.evaluate()
            if self._lisitify_flag:
                return '(%s, )' % v
            else:
                return '(%s)' % v
        else:
            return v

    def get_all_params(self, type):
        """
        Get all the params from the flowgraph that have the given type.

        Args:
            type: the specified type

        Returns:
            a list of params
        """
        params = []
        for block in self.parent_flowgraph.get_enabled_blocks():
            params.extend(p for p in block.params.values() if p.dtype == type)
        return params

    def is_enum(self):
        return self.dtype == 'enum'

    def get_value(self):
        value = self.value
        if self.is_enum() and value not in self.options:
            value = self.default
            self.set_value(value)
        return value

    def set_value(self, value):
        # Must be a string
        self.value = str(value)

    def set_default(self, value):
        if self.default == self.value:
            self.set_value(value)
        self.default = str(value)

    ##############################################
    # Import/Export Methods
    ##############################################
    def export_data(self):
        """
        Export this param's key/value.

        Returns:
            a nested data odict
        """
        n = collections.OrderedDict()
        n['key'] = self.key
        n['value'] = self.get_value()
        return n
