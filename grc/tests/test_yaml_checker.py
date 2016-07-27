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

from grc.core.utils.yaml_loader import GRCLoader
from grc.core.utils.yaml_checker import SchemaChecker

import yaml

BLOCK1 = """
key: block_key
name: testname

params:
-   key: vlen
    name: Vec Length
    dtype: int
    value: '1'
-   key: out_type
    name: Vec Length
    dtype: string
    value: complex
-   key: a
    name: Alpha
    dtype: !eval '(out_type)'
    value: '0'

sinks:
-   name: in
    domain: stream
    dtype: complex
    vlen: !eval '2 * vlen'
-   name: in2
    domain: message
    key: in2

sources:
-   name: out
    domain: stream
    dtype: !eval 'out_type'
    vlen: !eval 'vlen'

make: blocks.complex_to_mag_squared({vlen})
"""


def test_min():
    checker = SchemaChecker()
    assert checker.run({'key': 'test'})
    assert not checker.run({'name': 'test'})


def test_extra_keys():
    checker = SchemaChecker()
    assert checker.run({'key': 'test', 'abcdefg': 'nonsense'})
    assert checker.messages == [('block', 'warn', "Ignoring extra key 'abcdefg'")]


def test_checker():
    checker = SchemaChecker()
    data = yaml.load(BLOCK1, Loader=GRCLoader)
    passed = checker.run(data)
    if not passed:
        print()
        for msg in checker.messages:
            print(msg)

    assert passed, checker.messages
