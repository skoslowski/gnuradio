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

from .. flowgraph import FlowGraph
from .. blocks.variable import VariableBlock


def add_variable(fg, name, value):
    var = VariableBlock()
    var.params['uid'].value = name
    var.params['value'].value = value
    fg.add_block(var)


def test_flowgraph_namespace():
    fg = FlowGraph()
    add_variable(fg, "_", "A")  # to put A in namespace
    add_variable(fg, "A", "B+C")
    add_variable(fg, "B", "C")
    add_variable(fg, "C", "1")
    fg.update()
    assert fg.namespace == {"A": 2, "B": 1, "C": 1}
    assert fg.is_valid
    assert list(fg.namespace.keys()) == ['C', 'B', 'A']


def test_flowgraph_namespace_circle():
    fg = FlowGraph()
    add_variable(fg, "A", "B+C")
    add_variable(fg, "B", "C")
    add_variable(fg, "C", "A")
    fg.update()
    assert not fg.is_valid
    assert all("is not defined" in error.args[0]
               for origin, error in fg.iter_errors())

def test_flowgraph_missing_var():
    fg = FlowGraph()
    add_variable(fg, "A", "B")
    fg.update()
    assert not fg.is_valid


def test_flowgraph_invalid_var():
    fg = FlowGraph()
    add_variable(fg, "A", "1+")
    fg.update()
    assert not fg.is_valid


def test_flowgraph_imports():
    fg = FlowGraph()
    fg.options['imports'] = "import math; myfunc = int"
    add_variable(fg, "A", "math.sqrt(4) + myfunc(3.5)")
    add_variable(fg, "B", "myfunc(3.5)")
    add_variable(fg, "C", "math.sqrt(4)")
    fg.update()
    for key, value in {'A': 5, 'B': 3, 'C': 2}.iteritems():
        assert fg.namespace[key] == value
    assert fg.is_valid
