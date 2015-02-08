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
from itertools import ifilter as filter  # py3k default

from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import inspect

from .. import exceptions
from .. base import Element, Namespace
from .. params import Param, IdParam
from .. ports import (BasePort, StreamPort, MessagePort,
                      SINK, SOURCE, PORT_DIRECTIONS)


class BaseBlock(Element):
    """Basic element with parameters and import/make template"""
    __metaclass__ = ABCMeta

    label = 'Block'  # the label of this block (for the gui)
    categories = []  # categories put put this block under

    import_template = ''
    make_template = ''

    def __init__(self, **kwargs):
        super(BaseBlock, self).__init__()
        self._evaluated = None

        self.params = OrderedDict()
        self.namespace = Namespace(self.params)  # dict of evaluated params
        self.enabled = True

        self.add_param(cls=IdParam)
        # self.params['uid'].set_unique_block_id()
        self.setup(**kwargs)

    @abstractmethod
    def setup(self, **kwargs):
        """here block designers add code for ports and params"""
        pass

    @staticmethod
    def value(valid_params):
        """design-time value (as string) of this block/variable"""
        # todo: find a better way to spec a value a to signal NotImplemented
        return object()

    def add_param(self, *args, **kwargs):
        """Add a param to this block

        Usage options:
            - a param object as args[0]
            - a param class as kwargs['cls']
            - all other args and kwargs get passed to param constructor
        """
        if args and isinstance(args[0], Param):
            param = args[0]
        elif 'cls' in kwargs:
            cls = kwargs.pop('cls')  # remove cls from kwargs
            if inspect.isclass(cls) and issubclass(cls, Param):
                param = cls(*args, **kwargs)
            else:
                raise exceptions.BlockSetupException("Invalid param class")
        else:
            param = Param(*args, **kwargs)

        if param.uid in self.params:
            raise exceptions.BlockSetupException(
                "Param key '{}' not unique".format(param.uid))
        self.params[param.uid] = param
        self.add_child(param)  # double bookkeeping =(
        return param

    @property
    def uid(self):
        """unique identifier for this block within the flow-graph"""
        return self.params['uid'].value

    @property
    def evaluated(self):
        return self._evaluated

    def update(self):
        """Update the blocks params and (re-)build the local namespace"""
        self.namespace.clear()
        for key, param in self.params.iteritems():
            if key in self.namespace.auto_resolved_keys:
                continue  # already evaluated for some other param
            param.update()
            if param.is_valid:
                self.namespace[key] = param.evaluated
        if self.is_valid:
            try:
                value = self.value(self.namespace)
                self._evaluated = self.parent_flowgraph.evaluate(value) \
                    if isinstance(value, str) else value
            except Exception as e:
                self.add_error(e)

    def load(self, state):
        for key, param in self.params.iteritems():
            try:
                param.value = state[key]
                self.update()
            except KeyError:
                pass  # no state info for this param
        self.enabled = state['enabled']
        # todo: parse GUI state info

    def save(self):
        state = {
            key: param.value for key, param in self.params.iteritems()
        }
        state['enabled'] = self.enabled
        # ToDo: add gui stuff
        return state


class Block(BaseBlock):
    """A regular block (not a pad, virtual sink/source, variable)"""

    throttling = False  # is this a throttling block?

    def __init__(self, **kwargs):
        super(Block, self).__init__(**kwargs)

        # lists of active/expanded ports (think hidden ports, bus ports, nports)
        self.sources = []  # filled / updated by update()
        self.sinks = []

        self.add_param('alias', 'Block Alias', vtype=str, default=self.uid)
        # todo: hide these for blocks w/o ports (shouldn't be the case in this class)
        self.add_param('affinity', 'Core Affinity', vtype=list, default=[])
        # todo: hide these for sink-only blocks
        self.add_param('minoutbuf', 'Min Output Buffer', vtype=int, default=0)
        self.add_param('maxoutbuf', 'Max Output Buffer', vtype=int, default=0)

    def add_port(self, cls, *args, **kwargs):
        """Add a port to this block

        Args:
            - cls: instance or subclass of BasePort
            - args, kwargs: arguments to pass the the port
        """
        if inspect.isclass(cls) and issubclass(cls, BasePort):
            port = cls(*args, **kwargs)
        elif isinstance(cls, BasePort):
            port = cls
        else:
            raise ValueError("Excepted an instance or subclass of BasePort")
        if port.direction not in PORT_DIRECTIONS:
            raise exceptions.BlockSetupException("Unknown port direction")
        self.add_child(port)
        return port

    def iter_ports(self, direction=None):
        for port in filter(lambda p: isinstance(p, BasePort), self.children):
            if direction is None or port.direction == direction:
                yield port

    def update(self):
        """Update the blocks ports"""
        evaluated = super(Block, self).update()  # update param und evaluate first
        ports_current = {SINK: list(self.sinks), SOURCE: list(self.sources)}
        port_lists = {SINK: self.sinks, SOURCE: self.sources}
        del self.sinks[:]
        del self.sources[:]
        for port in self.iter_ports():
            port.update()  # todo: handle exceptions
            if port.active:
                # re-add ports and their clones
                ports = port_lists.get(port.direction, [])
                ports.append(port)
                ports += port.clones
            elif port in ports_current.get(port.direction, []):
                # remove connections from ports that were disabled
                port.disconnect()
        # todo: form busses
        return evaluated

    def add_stream_sink(self, label, dtype, vlen=1, nports=None):
        return self.add_port(StreamPort, 'sink', label, dtype, vlen, nports)

    def add_stream_source(self, label, dtype, vlen=1, nports=None):
        return self.add_port(StreamPort, 'source', label, dtype, vlen, nports)

    def add_message_sink(self, label, key=None, nports=1):
        return self.add_port(MessagePort, 'sink', label, key, nports)

    def add_message_source(self, label, key=None, nports=1):
        return self.add_port(MessagePort, 'source', label, key, nports)
