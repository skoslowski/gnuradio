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


class Message(collections.namedtuple('Message', 'path type message')):
    format = '{path}: {type}: {message}'

    def __str__(self):
        return self.format.format(**self._asdict())


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
    extra=dict,
)


PARAM_SCHEME = expand(
    key=Spec(types=str_, required=True, item_scheme=None),
    name=str_,
    dtype=str_,

    value=object,
    options=Spec(types=list, required=False, item_scheme=OPTIONS_SCHEME),

    category=str_,
    hide=str_,
)

PORT_SCHEME = expand(
    name=str_,
    key=str_,
    domain=str_,

    dtype=str_,
    vlen=(int, str_),
)

BLOCK_SCHEME = expand(
    key=Spec(types=str_, required=True, item_scheme=None),
    name=str_,
    category=(list, str_),
    flags=(list, str_),

    params=Spec(types=list, required=False, item_scheme=PARAM_SCHEME),
    sinks=Spec(types=list, required=False, item_scheme=PORT_SCHEME),
    sources=Spec(types=list, required=False, item_scheme=PORT_SCHEME),

    imports=(list, str),
    make=str_,

    callbacks=(list, str_),
    documentation=str_,
)


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

        for key, (types_, required, item_scheme) in six.iteritems(scheme):
            try:
                value = data[key]
            except KeyError:
                if required:
                    self._error('Missing required entry {!r}'.format(key))
                continue

            if not isinstance(value, types_):
                self._error('Value type {!r} for key {!r} not on valid types'.format(
                    type(value).__name__, key))

            if item_scheme and isinstance(value, types.ListType):
                self._check_items(value, item_scheme, label=key)

        for key in set(data).difference(scheme):
            self._warn('Ignoring extra key {!r}'.format(key))

    def _check_items(self, data, scheme, label):
        for i, item in enumerate(data):
            self._path.append('{}[{}]'.format(label, i))
            self._check(item, scheme)
            self._path.pop()

    def _error(self, msg):
        self.messages.append(Message('.'.join(self._path), 'error', msg))
        self.passed = False

    def _warn(self, msg):
        self.messages.append(Message('.'.join(self._path), 'warn', msg))
