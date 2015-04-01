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

import functools

from . import exceptions
from . import base
from . blocks import BaseBlock
from . connection import Connection


def functools_lru_cache(func):
    """very simplified back-port of functools.lru_cache in py3k"""
    result_cache = {}

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        key = str(args[0])
        try:
            result = result_cache[key]
        except KeyError:
            result = result_cache[key] = func(self, *args, **kwargs)
        return result

    wrapper.cache_clear = result_cache.clear
    return wrapper


class FlowGraph(base.Element):

    def __init__(self):
        super(FlowGraph, self).__init__()

        self.blocks = []
        self.connections = []

        self.options = {}  # do we want a dict here?
        self.namespace = base.Namespace(self.blocks)

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
                block = self.platform.blocks[key_or_block]()
            except KeyError:
                raise exceptions.BlockException(
                    "Failed to add block {!r}".format(key_or_block))
        elif isinstance(key_or_block, BaseBlock):
            block = key_or_block
        else:
            raise exceptions.BlockException("")
        self.add_child(block)
        self.blocks.append(block)
        return block

    def make_connection(self, endpoint_a, endpoint_b):
        """Add a connection between the ports of two blocks"""
        connection = Connection(endpoint_a, endpoint_b)
        self.add_child(connection)
        self.connections.append(connection)
        return connection

    def remove(self, elements):
        for element in elements:
            if isinstance(element, BaseBlock):
                # todo: remove connections to this block?
                self.blocks.remove(element)
            elif isinstance(element, Connection):
                self.connections.remove(element)
            self.children.remove(element)
            del element

    @functools_lru_cache
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
            block.update()

        self.blocks.sort(key=index_default(self.namespace.auto_resolved_keys))

        for connection in self.connections:
            connection.update()


def index_default(mylist, default=None):
    if default is None:
        default = len(mylist)

    def index_getter(element):
        try:
            return mylist.index(element.name)
        except:
            return default
    return index_getter
