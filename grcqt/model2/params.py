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

from __future__ import absolute_import, division, print_function

import re
from abc import ABCMeta
from itertools import imap, count

from . import exceptions, types
from . base import ElementWithUpdate
from . _consts import BLOCK_ID_BLACK_LIST


class Param(ElementWithUpdate):
    __metaclass__ = ABCMeta

    def __init__(self, parent, name, key, vtype=None, default=None, category=None, validator=None):
        super(Param, self).__init__(parent)
        self._key = key
        self._vtype = None
        self._evaluated = None

        self.name = name
        self.category = category
        self.vtype = vtype
        self.validator = validator
        self.value = self.default = default  # todo get vtype default

    @property
    def key(self):
        return self._key

    @property
    def vtype(self):
        return self._vtype

    @vtype.setter
    def vtype(self, value):
        assert value in types.param_vtypes, "Invalid vtype '{}'".format(value)
        self._vtype = value

    @property
    def evaluated(self):
        return self._evaluated

    def reset(self):
        self.value = self.default

    def update(self):
        # first update type, name, visibility, ..
        super(Param, self).update()
        # then get evaluated value. 'parse' adds quotes or puts it in a list
        self._evaluated = types.param_vtypes[self.vtype].parse(
            self.parent_flowgraph.evaluate(self.value))

    def validate(self):
        try:
            # value type validation
            types.param_vtypes[self.vtype].validate(self.evaluated)
            # custom validator
            if callable(self.validator) and not self.validator(self.evaluated):
                self.add_error_message("Custom validator for parameter"
                                       " '{self.name}' failed")
        except Exception as e:
            self.add_error_message("Failed to validate '{self.name}': " +
                                   e.args[0])


class IdParam(Param):
    """Parameter of a block used as a unique parameter within a flow-graph"""

    _id_matcher = re.compile('^[a-z|A-Z]\w*$')

    def __init__(self, parent):
        super(IdParam, self).__init__(parent, 'ID', 'id', str)
        self.value = self.default = self._get_unique_block_id()

    def _get_unique_block_id(self):
        """get a unique block id within the flow-graph by trail&error"""
        blocks = self.parent_flowgraph.blocks
        block_name = self.parent_block.__class__.__name__
        get_block_id = lambda key: "{}_{}".format(block_name, key)
        for block_id in imap(get_block_id, count()):
            if block_id not in blocks:
                return repr(block_id)

    def validate(self):
        id_value = self.evaluated
        is_duplicate_id = any(
            block.id == id_value
            for block in self.parent_flowgraph.blocks if block is not self
        )
        if not self._id_matcher.match(id_value):
            self.add_error_message("Invalid ID")
        elif id_value in BLOCK_ID_BLACK_LIST:
            self.add_error_message("ID is blacklisted")
        elif is_duplicate_id:
            self.add_error_message("Duplicate ID")
        super(IdParam, self).validate()


class OptionsParam(Param):

    class Option(object):
        """
        Each option has a name and value. alternate values may be passed
        """
        def __init__(self, name, value, **kwargs):
            self.name = name
            self.value = value
            for key in kwargs:
                setattr(self, key, kwargs[key])

        def __format__(self, format_spec):
            return str(self.value)

    def __init__(self, parent, name, key, vtype, default=None):
        super(OptionsParam, self).__init__(parent, name, key, vtype, default)
        self.options = []
        self.allow_arbitrary_values = False

    def add_option(self, name_or_option, value, **kwargs):
        if isinstance(name_or_option, self.Option):
            option = name_or_option
        else:
            option = self.Option(name_or_option, value, **kwargs)
        self.options.append(option)

    def update(self):
        super(Param, self).update()
        self._evaluated = self.parent_flowgraph.evaluate(self.value)

    def validate(self):
        super(OptionsParam, self).validate()
        value = self.evaluated
        if not self.allow_arbitrary_values and value not in imap(lambda o: o.value, self.options):
            self.add_error_message("Value '{}' not allowed".format(value))

    def __format__(self, format_spec):
        return self.evaluated.__format__(format_spec)

    def __getitem__(self, key):
        return self.options[self.options.index(self.evaluated)].extra[key]
