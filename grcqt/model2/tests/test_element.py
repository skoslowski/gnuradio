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

from .. base import Element, ElementWithUpdate
from .. blocks import BaseBlock


def test_element():
    class T(Element):
        pass

    class T2(Element):
        pass

    a = T(None)
    b = T2(a)
    c = T2(a)
    d = T(c)
    e = T(d)

    assert isinstance(a, Element)
    assert b.parent == a
    assert c.parent == a
    assert d.parent == c
    assert a.children == [b, c]
    assert c.children == [d]
    assert d.get_parent_by_class(T2) == c
    assert e.get_parent_by_class(T2) == c
    assert d.get_parent_by_class(T) == a
    assert c.get_parent_by_class(T2) is None


def test_element_update():
    class Block(Element):
        namespace = {'test': 3, 'on': True}
    BaseBlock.register(Block)

    class A(ElementWithUpdate):
        a = 3
        _b = False

        @property
        def b(self):
            return self._b

        @b.setter
        def b(self, value):
            if type(value) == bool:
                self._b = value
            else:
                raise ValueError("wrong type")
    b = Block(None)
    a = A(b)
    a.on_update(a=lambda test, **kwargs: test+1, b='on')

    assert a.a == 3 and not a.b
    a.update()
    assert a.is_valid and a.a == 4 and a.b

    b.namespace['on'] = 1
    a.update()
    assert not a.is_valid and a.b
    assert 'wrong type' in a.error_messages[-1]
