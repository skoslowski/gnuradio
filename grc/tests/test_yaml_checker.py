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
id: block_key
label: testname

parameters:
-   id: vlen
    label: Vec Length
    dtype: int
    default: 1
-   id: out_type
    label: Vec Length
    dtype: string
    default: complex
-   id: a
    label: Alpha
    dtype: ${ out_type }
    default: '0'

inputs:
-   label: in
    domain: stream
    dtype: complex
    vlen: ${ 2 * vlen }
-   name: in2
    domain: message
    id: in2

outputs:
-   label: out
    domain: stream
    dtype: ${ out_type }
    vlen: ${ vlen }

templates:
    make: blocks.complex_to_mag_squared(${ vlen })
"""


def test_min():
    checker = SchemaChecker()
    assert checker.run({'id': 'test'})
    assert not checker.run({'name': 'test'})


def test_extra_keys():
    checker = SchemaChecker()
    assert checker.run({'id': 'test', 'abcdefg': 'nonsense'})
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
