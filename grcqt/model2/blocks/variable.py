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

from ..block import BaseBlock


class VariableBlock(BaseBlock):

    label = "Variable"

    def __repr__(self):
        return "<{} {!r}>".format(self.label, self.name)

    def setup(self, **kwargs):
        self.add_param("value", "Value", "raw")

    @staticmethod
    def value(valid_params):
        try:
            return valid_params['value']
        except KeyError:
            raise ValueError("Value undefined")
