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

from __future__ import absolute_import

import os
import logging

from . import block_tree, block_xml

path = os.path
logger = logging.getLogger(__name__)


class Converter(object):

    def __init__(self, search_path, output_dir='~/.cache/grc_gnuradio', force=False):
        self.search_path = search_path
        self.output_dir = output_dir

        self.force = force

        converter_module_path = path.dirname(__file__)
        self._converter_mtime = max(path.getmtime(path.join(converter_module_path, module))
                                    for module in os.listdir(converter_module_path))

    def run(self):
        if not path.isdir(self.output_dir):
            os.makedirs(self.output_dir)
        for xml_file in self.iter_files_in_block_path():
            if xml_file.endswith("block_tree.xml"):
                self.load_category_tree_xml(xml_file)
            elif xml_file.endswith('domain.xml'):
                pass
            else:
                self.load_block_xml(xml_file)

    def load_block_xml(self, xml_file):
        """Load block description from xml file"""
        if 'qtgui_' in xml_file or '.grc_gnuradio/' in xml_file:
            return

        key_from_xml = path.basename(xml_file)[:-4]
        yml_file = path.join(self.output_dir, key_from_xml + '.block.yml')

        if not self.needs_conversion(xml_file, yml_file):
            return  # yml file up-to-date

        # print('Converting', xml_file)
        key, data = block_xml.convert(xml_file)
        # if key_from_xml != key:
        #     print('Warning: key is not filename in', xml_file)
        with open(yml_file, 'w') as yml_file:
            yml_file.write(data)

    def load_category_tree_xml(self, xml_file):
        """Validate and parse category tree file and add it to list"""
        module_name = path.basename(xml_file)[:-len('block_tree.xml')].rstrip('._-')
        yml_file = path.join(self.output_dir, module_name + '.tree.yml')

        if not self.needs_conversion(xml_file, yml_file):
            return  # yml file up-to-date

        data = block_tree.convert(xml_file)
        with open(yml_file, 'w') as yml_file:
            yml_file.write(data)

    def needs_conversion(self, source, destination):
        """Check if source has already been converted and destination is up-to-date"""
        if self.force or not path.exists(destination):
            return True
        xml_time = path.getmtime(source)
        yml_time = path.getmtime(destination)

        return yml_time < xml_time or yml_time < self._converter_mtime

    def iter_files_in_block_path(self, suffix='.xml'):
        """Iterator for block descriptions and category trees"""
        for block_path in self.search_path:
            if path.isfile(block_path):
                yield block_path
            elif path.isdir(block_path):
                for root, _, files in os.walk(block_path, followlinks=True):
                    for name in files:
                        if name.endswith(suffix):
                            yield path.join(root, name)
            else:
                logger.warning('Invalid entry in search path: {}'.format(block_path))
