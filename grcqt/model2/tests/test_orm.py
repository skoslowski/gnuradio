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


class Param():
    def __init__(self, a):
        self.a = a

class DeclarativeMeta(type):

    def __new__(meta, name, bases, dct):
        dct['_params'] = {}
        for key in list(dct):
            if isinstance(dct[key], Param):
                dct['_params'][key] = dct.pop(key).a
        return super(DeclarativeMeta, meta).__new__(meta, name, bases, dct)

    def __setattr__(cls, key, value):
        if isinstance(value, Param):
            cls._params[key] = value.a
        else:
            type.__setattr__(cls, key, value)


class Block():
    __metaclass__ = DeclarativeMeta


def test_orm():

    class MyBlock(Block):
        a = Param("String")
    MyBlock.b = Param("test")

    assert MyBlock._params == {'a': 'String', 'b': 'test'}
    assert not hasattr(MyBlock, 'a')
    assert not hasattr(MyBlock, 'b')
