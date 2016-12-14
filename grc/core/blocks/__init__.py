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

from ._flags import Flags
from .block import Block
from .embedded_python import EPyBlock
from .dummy import DummyBlock


def build(id, label='', category='', flags='', documentation='',
          parameters=None, inputs=None, outputs=None, templates=None, **kwargs):
    block_cls = type(id, (Block,), {})
    block_cls.key = id

    block_cls.label = label or id.title()
    block_cls.category = [cat.strip() for cat in category.split('/') if cat.strip()]
    block_cls.flags = Flags(flags)
    block_cls.documentation = {'': documentation.strip('\n\t ').replace('\\\n', '')}

    templates = templates or {}
    block_cls.templates = {
        'imports': templates.get('imports', ''),
        'make': templates.get('make', ''),
        'callbacks': templates.get('callbacks', []),
        'var_make': templates.get('var_make', ''),
    }
    block_cls.parameters_data = parameters or []
    block_cls.inputs_data = inputs or []
    block_cls.outputs_data = outputs or []
    block_cls.extra_data = kwargs

    return block_cls
