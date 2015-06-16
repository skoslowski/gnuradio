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

from . import exceptions, base, blocks, connection


class FlowGraph(base.Element):

    def __init__(self, block_library=None):
        super(FlowGraph, self).__init__()

        self.block_library = block_library
        self.blocks = []
        self.connections = []

        self.options = {}  # do we want a dict here?
        self.namespace = base.Namespace(self.blocks)

    @classmethod
    def flowgraph_from_nested_data(cls, n, block_library=None):
        fg = cls(block_library)
        for blk in n.get('block', []):
            fg.add_block(blk['key']).load(blk.get('param', []))
        for con in n.get('connection', []):
            fg.make_connection(
                (con['source_block_id'], con['source_key']),
                (con['sink_block_id'], con['sink_key'])
            )
        fg.update()
        return fg

    @property
    def name(self):
        return self.options.get('name', 'Flowgraph')

    def add_block(self, key_or_block):
        """Add a new block to the flow-graph

        Args:
            key: the blocks key (a Block object can be passed as well)

        Raises:
            BlockException
        """
        if isinstance(key_or_block, str):
            try:
                block = self.block_library.blocks[key_or_block]()
            except KeyError:
                raise exceptions.BlockSetupError(
                    "Failed to add block {!r}".format(key_or_block))
        elif isinstance(key_or_block, blocks.BaseBlock):
            block = key_or_block
        else:
            raise exceptions.BlockSetupError("Need to block key or obj")
        self.add_child(block)
        self.blocks.append(block)
        return block

    def make_connection(self, endpoint_a, endpoint_b):
        """Add a connection between the ports of two blocks"""
        con = connection.Connection(endpoint_a, endpoint_b)
        self.add_child(con)
        self.connections.append(con)
        return con

    def remove(self, elements):
        if not isinstance(elements, (list, tuple)):
            elements = elements,
        for element in elements:
            if isinstance(element, blocks.BaseBlock):
                # todo: remove connections to this block?
                self.blocks.remove(element)
            elif isinstance(element, connection.Connection):
                self.connections.remove(element)
            self.children.remove(element)
            del element

    @base.functools_lru_cache
    def evaluate(self, expr):
        """Evaluate an expr in the flow-graph namespace"""
        return eval(str(expr), None, self.namespace)

    def update(self):
        self.evaluate.cache_clear()
        self.namespace.clear()
        try:
            with self.namespace.auto_resolve_off():
                exec(self.options.get('imports', ''), None, self.namespace)
        except Exception as e:
            self.add_error(e)

        # eval blocks first, then connections
        for block in self.blocks:
            if block.name in self.namespace.auto_resolved_keys:
                continue  # already evaluated for some other block
            block_evaluated = block.update()
            if block.name in self.namespace:
                block.add_error(Exception("Duplicate block name"))
            elif block.is_valid and block_evaluated is not base.NO_VALUE:
                self.namespace[block.name] = block_evaluated

        self.blocks.sort(key=index_default(self.namespace.auto_resolved_keys))

        for con in self.connections:
            con.update()


def index_default(mylist, default=None):
    if default is None:
        default = len(mylist)

    def index_getter(element):
        try:
            return mylist.index(element.name)
        except ValueError:
            return default
    return index_getter
