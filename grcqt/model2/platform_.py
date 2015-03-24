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

import os
import imp
import inspect
from itertools import imap
from collections import defaultdict

from . _consts import BLOCK_CLASS_FILE_EXTENSION, BLOCK_XML_EXTENSION, BLOCK_TREE_EXTENSION
from . import legacy
from . flowgraph import FlowGraph
from . blocks import BaseBlock


class BlockLoadException(Exception):
    pass


class Platform(object):

    def __init__(self, version, block_paths):
        """
        A platform object holds block classes.

        Args:
            version: a 3-tuple for file versions, e.g. (3,7,6)
            block_paths: the file paths to blocks in this platform
        """
        self.version = version
        self.block_paths = block_paths if not isinstance(block_paths, str) \
            else [block_paths]

        self.blocks = {}

    @property
    def version_short(self):
        return '.'.join(self.version)

    def load_blocks(self, block_paths=None):
        """load the blocks and block tree from the search paths"""
        block_paths = block_paths or self.block_paths
        categories = defaultdict(set)
        exceptions = []

        # first, load category tree files
        for block_tree_file in self.iter_block_files(block_paths, BLOCK_TREE_EXTENSION):
            try:
                for key, category in legacy.load_category_tree_xml(block_tree_file):
                    categories[key].update(category)
            except BlockLoadException as e:
                exceptions.append(e)

        # then load block definitions
        self.blocks.clear()
        for block_file in self.iter_block_files(block_paths, (BLOCK_XML_EXTENSION, BLOCK_CLASS_FILE_EXTENSION)):
            if block_file.endswith(BLOCK_TREE_EXTENSION):
                continue
            try:
                if block_file.endswith(BLOCK_XML_EXTENSION):
                    block = legacy.load_block_xml(block_file)
                    block.categories = categories[block.__name__].union(block.categories)
                    self.blocks[block.__name__] = block
                else:
                    self.load_block_class_file(block_file)

            except BlockLoadException as e:
                exceptions.append(e)
        if exceptions:
            raise BlockLoadException(exceptions)

    @staticmethod
    def iter_block_files(block_paths, suffix):
        """Iterator for block classes (legacy: block xml and category trees)"""
        expand_path = lambda x: os.path.abspath(os.path.expanduser(x))
        for block_path in imap(expand_path, block_paths):
            if os.path.isfile(block_path):
                yield block_path
            elif os.path.isdir(block_path):
                for dirpath, dirnames, filenames in os.walk(block_path):
                    for filename in sorted(filter(lambda f: f.endswith(suffix), filenames)):
                        yield os.path.join(dirpath, filename)

    def load_block_class_file(self, filename):
        """import filename and save all subclasses of Block in library"""
        f = None
        try:
            path, module_name = os.path.split(filename.rsplit('.py', 1)[0])
            f, filename, description = imp.find_module(module_name, [path] or None)
            module = imp.load_module("__grc__", f, filename, description)
            for key, value in vars(module).items():
                if inspect.isclass(value) and issubclass(value, BaseBlock):
                    # todo: check validity of Block class
                    if not getattr(value.setup, '__isabstractmethod__', False):
                        self.blocks[value.__name__] = value
        finally:
            if f: f.close()

    def flowgraph_from_nested_data(self, n):
        fg = FlowGraph(self)
        for blk in n.get('block', []):
            fg.add_block(blk['key']).load(blk.get('param', []))
        for con in n.get('connection', []):
            fg.make_connection(
                (con['source_block_id'], con['source_key']),
                (con['sink_block_id'], con['sink_key'])
            )
        return fg
