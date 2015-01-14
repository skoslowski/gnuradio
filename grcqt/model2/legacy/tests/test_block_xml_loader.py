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
from os import path
import glob

from lxml import etree
from StringIO import StringIO

from .. import load_block_xml
from .. block_xml_loader import Resolver, convert_cheetah_template


def iter_resource_files():
    test_file_dir = path.join(path.dirname(__file__), 'resources')
    for filename in glob.iglob(path.join(test_file_dir, '*.xml')):
        with open(filename) as fp:
            yield fp


def test_block_xml():
    for fp in iter_resource_files():
        BlockClass = load_block_xml(fp)
        #print BlockClass


@pytest.fixture
def resolver():
    xml = etree.parse(StringIO("""
        <block>
            <param><key>t1</key><value>t11</value></param>
            <param><key>t2</key><value>t21</value></param>
            <param><key>t3</key><option>
                <key>t31</key>
                <opt>a:123</opt><opt>bb:456</opt>
            </option></param>
            <test1>a</test1><test3>$t1</test3>
        </block>
    """))
    return Resolver(xml)


def test_resolver_param_defaults(resolver):
    assert str(resolver.params['t3']) == 't31'
    assert resolver.params['t3'].a == '123'
    assert resolver.params['t3'].bb == '456'

def test_resolver_fixed_value(resolver):
    assert resolver._eval('p1', 'no dollar sign in here') == 'no dollar sign in here'


def test_resolver_simple_template(resolver):
    assert resolver._eval('test', "$t1") == 't11'
    # pop the update action
    assert resolver.pop_on_update_kwargs() == dict(test='t1')
    # make sure its gone
    assert resolver.pop_on_update_kwargs() == dict()


def test_resolver_get(resolver):
    assert resolver.findtext('test1') == 'a'


def test_resolver_eval(resolver):
    assert resolver.eval('test3', 't') == 't11'
    assert resolver.pop_on_update_kwargs() == dict(t='t1')


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
    make = convert_cheetah_template("{test$a} $(abc123_a3) ${a}a $[a]lk $(b.cd)")
    assert make == "{{test{a}}} {abc123_a3} {a}a {a}lk {b.cd}"


def test_convert_cheetah_template2():
    make = convert_cheetah_template("[$abc] $test]")
    assert make == "[{abc}] {test}]"
