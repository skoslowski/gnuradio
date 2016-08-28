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

from __future__ import print_function

import types
import collections

import six

Spec = collections.namedtuple('Spec', 'types required item_scheme')


def expand(**kwargs):
    def expand_spec(spec):
        if not isinstance(spec, Spec):
            types_ = spec if isinstance(spec, tuple) else (spec,)
            spec = Spec(types=types_, required=False, item_scheme=None)
        elif not isinstance(spec.types, tuple):
            spec = Spec(types=(spec.types,), required=spec.required,
                        item_scheme=spec.item_scheme)
        return spec
    return {key: expand_spec(value) for key, value in kwargs.items()}

str_ = six.string_types


OPTIONS_SCHEME = expand(
    name=str_,
    value=object,
    attributes=dict,
)

PARAM_SCHEME = expand(
    base_key=str_,   # todo: rename/remove

    label=str_,
    category=str_,

    dtype=str_,
    default=object,
    options=Spec(types=list, required=False, item_scheme=OPTIONS_SCHEME),

    hide=str_,
)

PORT_SCHEME = expand(
    label=str_,
    domain=str_,

    key=str_,
    dtype=str_,
    vlen=(int, str_),

    multiplicity=(int, str_),
    optional=(bool, int, str_),
    hide=(bool, str_),
)

TEMPLATES_SCHEME = expand(
    imports=(list, str),
    var_make=str_,
    make=str_,
    callbacks=(list, str_),
)

BLOCK_SCHEME = expand(
    key=Spec(types=str_, required=True, item_scheme=None),
    label=str_,
    category=(list, str_),
    flags=(list, str_),

    params=Spec(types=list, required=False, item_scheme=(str_, PARAM_SCHEME)),
    sinks=Spec(types=list, required=False, item_scheme=PORT_SCHEME),
    sources=Spec(types=list, required=False, item_scheme=PORT_SCHEME),

    checks=(list, str_),
    value=str_,

    templates=Spec(types=dict, required=False, item_scheme=TEMPLATES_SCHEME),

    documentation=str_,

    block_wrapper_path=str_,  # todo: rename/remove
    grc_source=str_,  # todo: rename/remove
    param_tab_order=(list, str_)  # todo: rename/remove
)


class Message(collections.namedtuple('Message', 'path type message')):
    fmt = '{path}: {type}: {message}'

    def __str__(self):
        return self.fmt.format(**self._asdict())


class SchemaChecker(object):

    def __init__(self):
        self._path = []
        self.messages = []
        self.passed = False

    def run(self, data):
        self._reset()
        self._path.append('block')
        self._check(data, BLOCK_SCHEME)
        self._path.pop()
        return self.passed

    def _reset(self):
        del self.messages[:]
        del self._path[:]
        self.passed = True

    def _check(self, data, scheme):
        if not data or not isinstance(data, types.DictType):
            self._error('Empty data or not a dict')
            return
        if isinstance(scheme, types.DictType):
            self._check_dict(data, scheme)
        else:
            self._check_var_key_dict(data, *scheme)

    def _check_var_key_dict(self, data, key_type, value_scheme):
        for key, value in six.iteritems(data):
            if not isinstance(key, key_type):
                self._error('Key type {!r} for {!r} not in valid types'.format(
                    type(value).__name__, key))
            self._check_dict(value, value_scheme)

    def _check_dict(self, data, scheme):
        for key, (types_, required, item_scheme) in six.iteritems(scheme):
            try:
                value = data[key]
            except KeyError:
                if required:
                    self._error('Missing required entry {!r}'.format(key))
                continue

            self._check_value(value, types_, item_scheme, label=key)

        for key in set(data).difference(scheme):
            self._warn('Ignoring extra key {!r}'.format(key))

    def _check_list(self, data, scheme, label):
        for i, item in enumerate(data):
            self._path.append('{}[{}]'.format(label, i))
            self._check(item, scheme)
            self._path.pop()

    def _check_value(self, value, types_, item_scheme, label):
        if not isinstance(value, types_):
            self._error('Value type {!r} for {!r} not in valid types'.format(
                type(value).__name__, label))
        if item_scheme:
            if isinstance(value, types.ListType):
                self._check_list(value, item_scheme, label)
            elif isinstance(value, types.DictType):
                self._check_dict(value, item_scheme)

    def _error(self, msg):
        self.messages.append(Message('.'.join(self._path), 'error', msg))
        self.passed = False

    def _warn(self, msg):
        self.messages.append(Message('.'.join(self._path), 'warn', msg))
