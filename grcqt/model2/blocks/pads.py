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
import abc

from . base import BaseBlock


class PadBlock(BaseBlock):
    """
    Used to define the external IO of a generated hier block
    """
    label = 'Pad Block'  # the label of this block (label in the gui)
    categories = []

    @abc.abstractmethod
    def setup(self, **kwargs):
        self.add_param("nports", label="Number of ports", vtype=int, default=1)
        self.add_param("dtype", label="Port type", vtype=str, default="complex")
        self.add_param("vlen", label="VLEN", vtype=int, default=1)


class PadSource(BaseBlock):
    """
    Used to define the external IO of a generated hier block
    """
    label = 'Pad Source'  # the label of this block (label in the gui)
    categories = []

    @abc.abstractmethod
    def setup(self, **kwargs):
        super(PadSource, self).setup(self, **kwargs)
        self.add
