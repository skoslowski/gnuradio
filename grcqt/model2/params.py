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

from __future__ import absolute_import, division, print_function
from itertools import imap as map

import re
import itertools
from abc import ABCMeta

from . import types
from . base import ElementWithUpdate, NO_VALUE, BLOCK_ID_BLACK_LIST


class Param(ElementWithUpdate):
    __metaclass__ = ABCMeta
    _update_allowed = ['vtype', 'label', 'state']

    def __init__(self, name, label, vtype='raw', default=None, category=None, validator=None):
        super(Param, self).__init__()
        self._vtype = None

        self.name = name
        self.label = label if label is not None else name
        self.category = category
        self.vtype = vtype
        self.validator = validator
        self.value = self.default = default  # todo get vtype default

        self.state = 'show'

    def __repr__(self):
        return "<Param '{}.{}' = {!r}>".format(
            self.parent_block.name, self.name, self.value)

    @property
    def vtype(self):
        return self._vtype

    @vtype.setter
    def vtype(self, value):
        assert value in types.param_vtypes, "Invalid vtype '{}'".format(value)
        self._vtype = value

    def reset(self):
        self.value = self.default

    def update(self):
        # first update type, name, visibility, ..
        super(Param, self).update()
        # then get evaluated value. 'parse' adds quotes or puts it in a list
        if not self.is_valid:
            self.add_error("Can't evaluate invalid param")
            return NO_VALUE

        try:
            evaluated = types.param_vtypes[self.vtype].parse(
                self.parent_flowgraph.evaluate(self.value))
            # value type validation
            types.param_vtypes[self.vtype].validate(evaluated)
            # custom validator
            if callable(self.validator) and not self.validator(evaluated):
                raise Exception("Custom validator for parameter"
                                " '{self.label}' failed")
        except Exception as e:
            self.add_error(e)
            evaluated = NO_VALUE

        return evaluated


class NameParam(Param):
    """Parameter of a block used as a unique parameter within a flow-graph"""

    _update_allowed = []
    _name_matcher = re.compile('^[a-z|A-Z]\w*$')
    _name_factory = map(lambda c: repr("block_{}".format(c)),itertools.count())

    def __init__(self):
        super(NameParam, self).__init__('name', label='ID', vtype=str)
        self.value = self.default = self._name_factory.next()

    @property
    def evaluated(self):
        return str(self.value).strip('\'\"')

    def update(self):
        evaluated = self.evaluated
        if not self._name_matcher.match(evaluated):
            self.add_error(Exception("Invalid ID {!r}".format(evaluated)))
        elif evaluated in BLOCK_ID_BLACK_LIST:
            self.add_error("ID is blacklisted")

        return NO_VALUE  # Never add this to the block namespace


class OptionsParam(Param):

    class Option(object):
        """
        Each option has a label and value. alternate values may be passed
        """
        def __init__(self, label, value, **kwargs):
            self.label = label
            self.value = value
            for key in kwargs:
                setattr(self, key, kwargs[key])

        def __format__(self, format_spec):
            return str(self.value)

    def __init__(self, name, label=None, vtype='raw', default=None):
        super(OptionsParam, self).__init__(name, label, vtype, default)
        self.options = []
        self.allow_arbitrary_values = False
        self._evaluated = NO_VALUE

    def add_option(self, name_or_option, value, **kwargs):
        if isinstance(name_or_option, self.Option):
            option = name_or_option
        else:
            option = self.Option(name_or_option, value, **kwargs)
        self.options.append(option)

    def update(self):
        evaluated = super(Param, self).update()
        if not self.allow_arbitrary_values and \
                        evaluated not in map(lambda o: o.value, self.options):
            self.add_error("Value {self.evaluated!r} not allowed")

        self._evaluated = evaluated
        return evaluated

    def __format__(self, format_spec):
        return self._evaluated.__format__(format_spec)

    def __getitem__(self, key):
        return self.options[self.options.index(self._evaluated)].extra[key]


class DTypeParam(OptionsParam):
    pass
    # ToDo: Implement


class VlenParam(Param):

    def __init__(self, name="vlen", label="VLEN", vtype='int', default=1,
                 validator=lambda v: v>0):
        super(VlenParam, self).__init__(name, label, vtype, default, validator)
