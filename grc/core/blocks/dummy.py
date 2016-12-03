# Copyright 2016 Free Software Foundation, Inc.
# This file is part of GNU Radio
#
# GNU Radio Companion is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# GNU Radio Companion is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

from __future__ import absolute_import

from .block import Block


class DummyBlock(Block):

    is_dummy_block = True
    build_in_param_keys = 'id alias affinity minoutbuf maxoutbuf comment'

    def __init__(self, parent, id, missing_block_id, params_n):
        super(DummyBlock, self).__init__(parent=parent, id=missing_block_id, label='Missing Block')
        param_factory = self.parent_platform.get_new_param
        for param_n in params_n:
            param_id = param_n['id']
            self.params.setdefault(param_id, param_factory(self, key=param_id, label=param_id, dtype='string'))

    def is_valid(self):
        return False

    @property
    def enabled(self):
        return False

    def add_missing_port(self, port_id, direction):
        port = self.parent_platform.get_new_port(
            parent=self, direction=direction, id=port_id, name='?', dtype='',
        )
        if port.is_source:
            self.sources.append(port)
        else:
            self.sinks.append(port)
        return port
