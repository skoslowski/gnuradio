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
    var.params['id'].value = name
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
    assert list(fg.namespace.keys()) == ['C', 'B', 'A']


def test_flowgraph_namespace_circle():
    fg = FlowGraph()
    add_variable(fg, "A", "B+C")
    add_variable(fg, "B", "C")
    add_variable(fg, "C", "A")
    try:
        fg.update()
    except NameError as e:
        assert e.args == ("name 'B' is not defined",)
    else:
        assert False


def test_flowgraph_missing_var():
    fg = FlowGraph()
    add_variable(fg, "A", "B")
    try:
        fg.update()
    except NameError as e:
        assert e.args == ("name 'B' is not defined",)
    else:
        assert False


def test_flowgraph_invalid_var():
    fg = FlowGraph()
    add_variable(fg, "A", "1+")
    try:
        fg.update()
    except SyntaxError:
        pass
    else:
        assert False
