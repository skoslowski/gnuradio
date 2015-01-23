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

import itertools
import numpy as np


port_dtypes = {}
param_vtypes = {}


class PortDType(object):

    def __init__(self, name, key, sizeof):
        self.name = name
        self.key = key
        self.sizeof = sizeof

    def __eq__(self, other):
        return hasattr(other, "sizeof") and self.sizeof == other.sizeof

    def __mul__(self, other):
        return self.sizeof * other

    @classmethod
    def register(cls, name, sizeof, keys):
        if not isinstance(keys, (list, set, tuple)):
            keys = (keys,)
        for key in keys:
            port_dtypes[key] = cls(name, keys[0], sizeof)


# build-in types
PortDType.register('Complex Float 64',   16, 'fc64')
PortDType.register('Complex Float 32',    8, ('fc64', 'complex', complex))

PortDType.register('Float 64',            8, 'f64')
PortDType.register('Float 32',            4, ('f32', 'float', float))

PortDType.register('Complex Integer 64', 16, 'sc64')
PortDType.register('Complex Integer 32',  8, 'sc32')
PortDType.register('Complex Integer 16',  4, 'sc16')
PortDType.register('Complex Integer 8',   2, 'sc8')

PortDType.register('Integer 64',          8, 's64')
PortDType.register('Integer 32',          4, ('s32', 'int', int))
PortDType.register('Integer 16',          2, ('s16', 'short'))
PortDType.register('Integer 8',           1, ('s8',  'byte'))  # uint?


class ParamVType(object):

    def __init__(self, names, valid_types):
        self.names = names if isinstance(names, (list, set, tuple)) else (names,)
        self.valid_types = valid_types

    def parse(self, evaluated):
        return evaluated

    def validate(self, evaluated):
        if not isinstance(evaluated, self.valid_types):
            raise TypeError("Expression '{}' is invalid for type {}".format(
                str(evaluated), self.names[0]
            ))

    @classmethod
    def register(cls, *args, **kwargs):
        vtype = cls(*args, **kwargs)
        for key in itertools.chain(vtype.names, vtype.valid_types):
            if key not in param_vtypes:
                param_vtypes[key] = vtype


class ParamRawVType(ParamVType):
    def validate(self, evaluated):
        return evaluated


class ParamStringVType(ParamVType):

    def parse(self, evaluated):
        if evaluated is None:
            return ''
        if not isinstance(evaluated, str):
            return repr(str(evaluated))


class ParamNumericVType(ParamVType):
    pass


class ParamVectorVType(ParamNumericVType):

    def __init__(self, names, valid_types, valid_item_types):
        super(ParamVectorVType, self).__init__(names, valid_types)
        self.valid_item_types = (
            valid_item_types if isinstance(names, (list, set, tuple)) else
            (valid_item_types,))

    def parse(self, evaluated):
        if not isinstance(evaluated, self.valid_types):
            evaluated = (evaluated, )
        return evaluated

    def validate(self, evaluated):
        if not all(isinstance(value, self.valid_item_types) for value in evaluated):
            raise TypeError("Expression '{}' is invalid for type {}".format(
                str(evaluated), self.names[0]
            ))


INT_TYPES = (int, long, np.int, np.int8, np.int16, np.int32, np.uint64,
             np.uint, np.uint8, np.uint16, np.uint32, np.uint64)
REAL_TYPES = (float, np.float, np.float32, np.float64) + INT_TYPES
COMPLEX_TYPES = (complex, np.complex, np.complex64, np.complex128) + REAL_TYPES
VECTOR_TYPES = (tuple, list, set, np.ndarray)

ParamVType.register('bool', (bool,))
ParamStringVType.register(('string', 'str'), (str,))
ParamRawVType.register('raw', (None,))

# the order if import here!
ParamNumericVType.register('int', INT_TYPES)
ParamNumericVType.register(('real', 'float'), REAL_TYPES)
ParamNumericVType.register('complex', COMPLEX_TYPES)

ParamVectorVType.register('complex_vector', VECTOR_TYPES, COMPLEX_TYPES)
ParamVectorVType.register(('real_vector', 'float_vector'), VECTOR_TYPES, REAL_TYPES)
ParamVectorVType.register('int_vector', VECTOR_TYPES, INT_TYPES)

