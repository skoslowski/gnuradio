"""
Copyright 2007-2011 Free Software Foundation, Inc.
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

from PyQt4.QtGui import *

from . Element import Element


class FlowGraph(QGraphicsScene, Element):

    def __init__(self):
        QGraphicsScene.__init__(self)
        Element.__init__(self)

    def add_new_block(self, key, coor=None):
        """
        Add a block of the given key to this flow graph.

        Args:
            key: the block key
            coor: an optional coordinate or None for random
        """

        id = self._get_unique_id(key)

        #calculate the position coordinate
        if coor is None:
            # ToDo: random position
            coor = 0, 0

        #get the new block
        block = self.get_new_block(key)
        block.setPos(coor)
        block.setRotation(0)
        block.get_param('id').set_value(id)

        self.addItem(block)

        return id


