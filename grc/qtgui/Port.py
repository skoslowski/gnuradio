from PyQt4.QtGui import *
from PyQt4.QtCore import Qt, QPointF

from .. base.Port import Port as _Port

from . FlowGraph import FlowGraph
from . import Colors

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
        self.text = QGraphicsTextItem(self)


    def updateLabel(self):
        self.setBrush(QColor(self.get_color()))
        self.text.setHtml(Utils.parse_template(PORT_MARKUP_TMPL, port=self))
        rect = self.text.shape().boundingRect()
        self.setRect(0, 0, rect.width(), rect.height())

    def updateSize(self, offset):
        if self.is_sink():
            x = -self.shape().boundingRect().width()
        else:
            x = self.parentItem().shape().boundingRect().width()

        self.setPos(x, offset)

        for con in self.get_connections():
            con.refresh()

    def connector_coordinate(self):
        return self.mapToScene(
            0.0 if self.is_sink() else self.shape().boundingRect().width(),
            self.shape().boundingRect().height() / 2.0
        )

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
