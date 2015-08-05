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

from ..block import Block


class PadStreamSource(Block):
    """
    Used to define the external IO of a generated hier block
    """
    label = 'Pad Stream Source'

    def setup(self, **kwargs):
        super(PadStreamSource,self).setup(**kwargs)

        self.add_param("label", label="Label", vtype=str, default="out")
        self.add_param("dtype", label="Port type", vtype=str, default="complex")
        self.add_param("vlen", label="VLEN", vtype=int, default=1,
                       validator=lambda v: v > 0)
        self.add_param("nports", label="Number of ports", vtype=int, default=1,
                       validator=lambda v: v > 0)

        self.add_stream_source().on_update("label", "dtype", "vlen", "nports")


class PadStreamSink(Block):
    """
    Used to define the external IO of a generated hier block
    """
    label = 'Pad Stream Sink'

    def setup(self, **kwargs):
        super(PadStreamSink, self).setup(**kwargs)

        self.add_param("label", label="Label", vtype=str, default="out")
        self.add_param("dtype", label="Port type", vtype=str, default="complex")
        self.add_param("vlen", label="VLEN", vtype=int, default=1)
        self.add_param("nports", label="Number of ports", vtype=int, default=1)

        self.add_stream_sink().on_update("label", "dtype", "vlen", "nports")


class PadMessageSource(Block):
    """
    Used to define the external IO of a generated hier block
    """
    label = 'Pad Message Source'

    def setup(self, **kwargs):
        super(PadMessageSource, self).setup(**kwargs)

        self.add_param("label", label="Label", vtype=str, default="out")
        self.add_param("key", label="Key", vtype=str, default="in")
        self.add_param("nports", label="Number of ports", vtype=int, default=1)

        self.add_message_sink().on_update("label", "dtype", "vlen", "nports")


class PadMessageSink(Block):
    """
    Used to define the external IO of a generated hier block
    """
    label = 'Pad Message Source'

    def setup(self, **kwargs):
        super(PadMessageSink, self).setup(**kwargs)

        self.add_param("label", label="Label", vtype=str, default="out")
        self.add_param("key", label="Key", vtype=str, default="in")
        self.add_param("nports", label="Number of ports", vtype=int, default=1)

        self.add_message_source().on_update("label", "dtype", "vlen", "nports")
