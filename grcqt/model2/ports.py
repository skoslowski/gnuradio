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

from abc import ABCMeta, abstractmethod
from itertools import islice

from . base import Element, ElementWithUpdate
from . import types


SINK = 'sink'
SOURCE = 'source'
PORT_DIRECTIONS = (SINK, SOURCE)


class BasePort(ElementWithUpdate):
    """Common elements of stream and message ports"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, direction, label, nports=None):
        super(BasePort, self).__init__()
        self._label = label
        self._nports = nports
        self.direction = direction
        self.active = True

    @property
    def label(self):
        """The label of this block"""
        label = self._label
        if self.nports is not None:
            label += '0'
        return label

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def nports(self):
        """Get nports, None means no cloning"""
        return self._nports

    @nports.setter
    def nports(self, nports):
        nports = int(nports)  # Can't go back to None
        assert nports is None or nports > 0, "Need nports > 0"
        self._nports = nports

    @property
    def allow_multiple_connections(self):
        return {SINK: False, SOURCE: True}.get(self.direction, False)

    @property
    def connections_optimal(self):
        return False

    @property
    def connections(self):
        """Iterator for the connections using this port"""
        for connection in self.parent_flowgraph.connections:
            if self in connection.ports:
                yield connection

    @property
    def clones(self):
        """Iterator for port clones of this (master) port"""
        for child in self.children:
            if isinstance(child, PortClone):
                yield child

    def disconnect(self):
        """remove all connections to/from this port"""
        for connection in self.connections:
            self.parent_flowgraph.remove(connection)

    def update(self):
        """update attributes, adjust the number of clones"""
        super(BasePort, self).update()  # used-installed callbacks
        if self.nports is not None:
            clones = list(self.clones)
            # remove excess clones
            for clone in islice(clones, self.nports-1, 1000000):
                clone.disconnect()
                self.children.remove(clone)
            # add new clones
            # since we only either remove or add clones, len(clones) is valid
            nports_current = len(clones) + 1
            for clone_id in range(nports_current, self.nports):
                self.add_child(PortClone(clone_id))

    def validate(self):
        """Assert that the port is connected correctly"""
        super(BasePort, self).validate()
        len_connections = len(list(self.connections))
        if not self.connections_optimal and not len_connections:
            error_message = "Port '{self.label}' not connected."
        elif len_connections > 1 and not self.allow_multiple_connections:
            error_message = "Port '{self.label}' has to many connections."
        else:
            error_message = ''
        self.add_error(error_message)


class PortClone(Element):
    """Acts as a clone of its parent object, but adds and index to its label"""

    def __init__(self, clone_id):
        super(PortClone, self).__init__()
        self.clone_id = clone_id

    @property
    def label(self):
        """The label of a cloned port gets its index appended"""
        return self.parent.label[:-1] + str(self.clone_id)

    @property
    def key(self):
        """The key of a cloned port gets its index appended"""
        if isinstance(self.parent, MessagePort):
            return self.parent.name + str(self.clone_id)

    def __getattr__(self, item):
        """Get all other attributes from parent (Port) object"""
        if item != 'clones':
            return getattr(self.parent, item)


BasePort.register(PortClone)


class StreamPort(BasePort):
    """Stream ports have a data type and vector length"""

    def __init__(self, direction, label, dtype='complex', vlen=1, nports=None):
        """Create a new stream port"""
        super(StreamPort, self).__init__(direction, label, nports)
        self._dtype = self._vlen = None
        # call setters
        self.dtype = dtype
        self.vlen = vlen

    @property
    def dtype(self):
        return self._dtype

    @dtype.setter
    def dtype(self, value):
        assert value in types.port_dtypes, "Invalid dtype '{}'".format(value)
        self._dtype = value

    @property
    def vlen(self):
        return self._vlen

    @vlen.setter
    def vlen(self, value):
        vlen = int(value)
        assert vlen > 0, "Invalid value '{}' for vlen".format(value)


class MessagePort(BasePort):
    """Message ports usually have a fixed key"""

    allow_multiple_connections = {SINK: False, SOURCE: True}
    connections_optimal = True

    def __init__(self, direction, label, key=None, nports=1):
        super(MessagePort, self).__init__(direction, label, nports)
        self.key = key or label

    @property
    def allow_multiple_connections(self):
        return True

    @property
    def connections_optimal(self):
        return True
