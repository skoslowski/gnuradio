from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

from .. base.Port import Port as _Port
from . FlowGraph import FlowGraph

import Utils

PORT_MARKUP_TMPL="""\
<span foreground="black" font_desc="Sans 7.5">$encode($port.get_name())</span>"""


class Port(QGraphicsRectItem, _Port):

    def __init__(self, block, n, dir):
        """
        Port constructor.
        Add graphics related params to the block.
        """

        QGraphicsRectItem.__init__(self, block)
        _Port.__init__(self, block, n, dir)

        if not isinstance(block.get_parent(), FlowGraph):
            return

        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsPanel)
        self.setBrush(QColor(255, 255, 0))

        self.text = QGraphicsTextItem(self)

    def updateLabel(self):
        self.text.setHtml(Utils.parse_template(PORT_MARKUP_TMPL, port=self))
        rect = self.text.shape().boundingRect()
        self.setRect(0, 0, rect.width(), rect.height())

    def updateSize(self, offset):
        if self.is_sink():
            x = -self.shape().boundingRect().width()
        else:
            x = self.parentItem().shape().boundingRect().width()

        self.setPos(x, offset)

    def get_connector_coordinate(self):
        return (10, 10)

    def get_connector_direction(self):
        """
        Get the direction that the socket points: 0,90,180,270.
        This is the rotation degree if the socket is an output or
        the rotation degree + 180 if the socket is an input.

        Returns:
        the direction in degrees
        """
        if self.is_source(): return self.get_rotation()
        elif self.is_sink(): return (self.get_rotation() + 180)%360

    def get_connector_length(self):
        """
        Get the length of the connector.
        The connector length increases as the port index changes.

        Returns:
        the length in pixels
        """
        return self._connector_length

    def get_rotation(self):
        """
        Get the parent's rotation rather than self.

        Returns:
        the parent's rotation
        """
        return self.get_parent().get_rotation()

    def move(self, delta_coor):
        """
Move the parent rather than self.

Args:
delta_corr: the (delta_x, delta_y) tuple
"""
        self.get_parent().move(delta_coor)

    def rotate(self, direction):
        """
Rotate the parent rather than self.

Args:
direction: degrees to rotate
"""
        self.get_parent().rotate(direction)

    def get_coordinate(self):
        """
Get the parent's coordinate rather than self.

Returns:
the parents coordinate
"""
        return self.get_parent().get_coordinate()

    def set_highlighted(self, highlight):
        """
Set the parent highlight rather than self.

Args:
highlight: true to enable highlighting
"""
        self.get_parent().set_highlighted(highlight)

    def is_highlighted(self):
        """
Get the parent's is highlight rather than self.

Returns:
the parent's highlighting status
"""
        return self.get_parent().is_highlighted()