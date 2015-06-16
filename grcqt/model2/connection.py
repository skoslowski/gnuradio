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

from . import exceptions, ports
from . base import Element


class Connection(Element):

    def __init__(self, port_a, port_b):
        super(Connection, self).__init__()
        if port_a.is_sink:
            port_a, port_b = port_b, port_a
        if not (port_a.is_source and port_b.is_source):
            raise ValueError("Can't make connection.")
        self.source_port = port_a
        self.sink_port = port_b

    @property
    def source_block(self):
        return self.source_port.parent_block

    @property
    def sink_block(self):
        return self.sink_port.parent_block

    @property
    def endpoints(self):
        return (
            (self.source_block, self.source_port),
            (self.sink_block, self.sink_port),
        )

    @property
    def ports(self):
        return self.source_port, self.sink_port

    def update(self):
        self.validate()

    def validate(self):
        source_port, sink_port = self.source_port, self.sink_port

        if isinstance(self.source_port, ports.StreamPort):
            if source_port.dtype != sink_port.dtype:
                self.add_error(exceptions.UpdateError("Data type mismatch"))
            elif source_port.itemsize != sink_port.itemsize:
                msg = "Item size mismatch: source has {}, sink {}".format(
                    source_port.itemsize, sink_port.itemsize)
                self.add_error(exceptions.UpdateError(msg))

