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

import pytest
from os import path
import glob
import textwrap

from lxml import etree


from grc.core.utils.block_xml_loader import (
    convert_cheetah_to_mako as to_mako,
    convert_cheetah_to_format_string,
    convert_xml
)


def test_cheetah_to_mako_simple():
    assert '${ te.st } ${ te_st } ${ test() }' == to_mako('${te.st} $[te_st] $test()')


def test_cheetah_to_mako_set():
    cheetah = textwrap.dedent("""
        #set $abs = 123
        $[working]
    """).strip()
    mako = textwrap.dedent("""
        <% abs = 123 %>
        ${ working }
    """).strip()

    assert mako == to_mako(cheetah)


# def test_cheetah_to_mako_inline_if():
#     cheetah = '#if $abc = 123 then "helo" else "eloh" #'
#     mako = ''
#     assert mako == to_mako(cheetah)


def test_block_xml():
    test_file_dir = path.join(path.dirname(__file__), 'resources')
    for filename in glob.iglob(path.join(test_file_dir, '*.xml')):
        with open(filename) as fp:
            convert_xml(fp)


def test_format():
    class A():
        value = "abc"
        elements = [1, 2, 3, 4]

        def __format__(self, spec):
            return self.value

        def __getitem__(self, key):
            return self.elements[key]

        def test(self):
            return "asdf"

    assert "{a} {a[0]}".format(a=A()) == "abc 1"


def test_convert_cheetah_template():
    make = convert_cheetah_to_format_string("{test$a} $(abc123_a3) ${a}a $[a]lk $(b.cd)")
    assert make == "{{test{a}}} {abc123_a3} {a}a {a}lk {b.cd}"


def test_convert_cheetah_template2():
    make = convert_cheetah_to_format_string("[$abc] $test]")
    assert make == "[{abc}] {test}]"


# def test_intree_xml():
#     test_file_dir = path.normpath(
#         path.join(path.dirname(__file__), '..', '..', 'gr-digital', 'grc')
#     )
#     for filename in glob.iglob(path.join(test_file_dir, '**.xml')):
#         with open(filename) as fp:
#             for line in fp:
#                 if '$' in line or '#' in line:
#                     print(line.rstrip())
#             # xml = etree.parse(fp).getroot()
#             # print(xml.findtext('make'))
