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


from lxml import etree

from ..block import Block
from ..legacy import block_xml_loader as xml_loader


reserved_block_keys = ('import', )  # todo: add more keys


def get_block_class(filename):
    try:
        with open(filename) as xml_file:
            xml = etree.parse(xml_file).getroot()
        # BLOCK_DTD.validate(xml)
    except (etree.LxmlError, OSError):
        raise

    block_e = xml_loader.Resolver(xml)

    class XMLBlock(Block):

        label = block_e.findtext('name')
        categories = block_e.findtext_all('category')

        throttling = block_e.findtext('throttle')

        import_template = block_e.findtext_all('import')
        make_template = xml_loader.get_make(block_e)
        callbacks = xml_loader.get_callbacks(block_e)

        doc=block_e.findtext('doc')

        def setup(self, **kwargs):
            """here block designers add code for ports and params"""
            for param, update in xml_loader.get_params(block_e):
                options = param.pop('options', [])
                p = self.add_param(**param).on_update(**update)
                for option in options:
                    p.add_option(**option)

            for direction in ('sink', 'source'):
                for method, port, update in xml_loader.get_ports(block_e, direction):
                    getattr(self, method)(**port).on_update(**update)

    key = block_e.findtext('key')
    if key in reserved_block_keys:
        key += '_'
    XMLBlock.__name__ == key

    return XMLBlock
