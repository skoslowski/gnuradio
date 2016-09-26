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

from __future__ import print_function

import glob

from os import path

from grc.core.legacy.block_xml_converter import convert_xml
from grc.core.legacy.yaml_output import yaml
from grc.core.schema_checker.yaml_checker import SchemaChecker


def test_block_xml():
    checker = SchemaChecker()
    test_file_dir = path.join(path.dirname(__file__), 'resources')
    for filename in glob.iglob(path.join(test_file_dir, '*.xml')):
        with open(filename) as fp:
            _, out = convert_xml(fp)
        print(out)
        data = yaml.load(out)
        passed = checker.run(data)
        assert passed, checker.messages
        assert not checker.messages
        # for r in messages:
        #     print(str(r)))
        # print('', '', out, sep='\n')


def test_format():
    class A(object):
        value = "abc"
        evaluated = "def"
        elements = {'b': 0}

        def __format__(self, spec):
            return self.value if spec != 'e' else self.evaluated

        def __getitem__(self, key):
            return self.elements[key]

        def __getattr__(self, name):
            return self.elements[name]

        def test(self):
            return "asdf"

    assert "{a} {a[b]} {a.b} {a:e}".format(a=A()) == "abc 0 0 def"


BLOCKS_PATHS = path.normpath(
    path.join(path.dirname(__file__), '..', '..', 'gr-**', 'grc', '*.xml')
)


# def test_intree_xml():
#     print()
#     for count, filename in enumerate(glob.iglob(BLOCKS_PATHS), 1):
#         # print(filename)
#         with open(filename) as fp:
#             out = convert_xml(fp)
#         data = yaml.load(out)
#         # print(data['make'])
#         params = {p['key']: p.get('default', '') for p in data.get('params', [])}
#
#         # ast.parse(data['make'].format(**params))
#         # print('', '', out, sep='\n')
