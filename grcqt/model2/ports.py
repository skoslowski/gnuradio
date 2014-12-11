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

from __future__ import absolute_import, division, print_function

from abc import ABCMeta, abstractmethod
from itertools import islice

from . base import Element, BlockChildElement
from . import types


class BasePort(BlockChildElement):
    """Common elements of stream and message ports"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, parent, name, nports=None, active=True):
        super(BasePort, self).__init__(parent)
        self._name = name
        self._nports = nports
        self.active = active

    @property
    def name(self):
        """The name of this block"""
        name = self._name
        if self.nports is not None:
            name += '0'
        return name

    @name.setter
    def name(self, name):
        self._name = name

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
        """adjust the number of clones"""
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
                PortClone(self, clone_id)  # ref kept in self.children


class PortClone(Element):
    """Acts as a clone of its parent object, but adds and index to its name"""

    def __init__(self, master_port, clone_id):
        super(PortClone, self).__init__(master_port)
        self.clone_id = clone_id

    @property
    def name(self):
        """The name of a cloned port gets its index appended"""
        return self.parent.name[:-1] + str(self.clone_id)

    @property
    def key(self):
        """The key of a cloned port gets its index appended"""
        if isinstance(self.parent, MessagePort):
            return self.parent.key + str(self.clone_id)

    def __getattr__(self, item):
        """Get all other attributes from parent (Port) object"""
        if item != 'clones':
            return getattr(self.parent, item)


BasePort.register(PortClone)


class StreamPort(BasePort):
    """Stream ports have a data type and vector length"""

    def __init__(self, parent, name, dtype, vlen=1, nports=None, active=True):
        """Create a new stream port"""
        super(StreamPort, self).__init__(parent, name, nports, active)
        self._dtype = None
        self._vlen = None
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

    def __init__(self, parent, name, key=None, nports=1, active=True):
        super(MessagePort, self).__init__(parent, name, nports, active)
        self.key = key or name
