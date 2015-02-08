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
from os import path

from .. platform import Platform


def test_block_load():
    test_file_dir = path.join(path.dirname(__file__), 'resources')

    p = Platform((3, 8, 0), test_file_dir)
    p.load_blocks()

    assert 'block_key' in p.blocks
    assert p.blocks['block_key'].label == "testname"

    assert 'test_block' in p.blocks


def test_block_load_for_real():
    return
    try:
        from gnuradio import gr
        prefs = gr.prefs()
        block_dir = prefs.get_string('grc', 'global_blocks_path', '')
    except ImportError:
        return

    p = Platform((3, 8, 0), block_dir)
    p.load_blocks()

    assert 'block_key' in p.blocks
    assert p.blocks['block_key'].label == "testname"

    assert 'test_block' in p.blocks
