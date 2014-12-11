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

import pytest

from .. flowgraph import FlowGraph
from .. blocks import Block


@pytest.fixture
def block():
    class MyBlock(Block):
        def setup(self, **kwargs):
            pass
    fg = FlowGraph()
    b = MyBlock(fg)
    b.add_stream_sink("in", complex)
    b.add_stream_sink("in2", dtype="int", nports=3)
    b.add_stream_sink("in3", complex)
    b.update()
    return b


def test_nports(block):
    """test the block fixture setup"""
    assert [sink.name for sink in block.sinks] == \
           ["in", "in20", "in21", "in22", "in3"]
    assert [sink.dtype for sink in block.sinks] == \
           [complex, "int", "int", "int", complex]


def test_set_nports(block):
    """test the block fixture setup"""
    try:
        block.sinks[1].nports = -1
    except AssertionError:
        pass
    else:
        assert False


def test_set_nports2(block):
    """test the block fixture setup"""
    try:
        block.sinks[1].nports = "NaN"
    except ValueError:
        pass
    else:
        assert False


def test_reduce_size(block):
    block.sinks[1].nports = 1
    block.update()
    assert [sink.name for sink in block.sinks] == ["in", "in20", "in3"]

    block.sinks[1].nports = 5
    block.update()
    assert [sink.name for sink in block.sinks] == \
           ["in", "in20", "in21", "in22", "in23", "in24", "in3"]

    block.sinks[1].nports = 2
    block.update()
    assert [sink.name for sink in block.sinks] == \
           ["in", "in20", "in21", "in3"]


def test_active(block):
    block._sinks[0].active = False
    block.update()
    assert [sink.name for sink in block.sinks] == \
           ["in20", "in21", "in22", "in3"]


def test_active2(block):
    block._sinks[1].active = False
    block.update()
    assert [sink.name for sink in block.sinks] == \
           ["in", "in3"]
    block._sinks[1].enabled = True
    block.update()
