from __future__ import division

from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

from . Element import Element
from .. base import odict
from Constants import \
	BLOCK_LABEL_PADDING, \
	PORT_SEPARATION, LABEL_SEPARATION, \
	PORT_BORDER_SEPARATION, POSSIBLE_ROTATIONS


class Block(QGraphicsRectItem, Element):
    """The graphical signal block."""

    def __init__(self, parent=None, scence=None):
        """
        Block contructor.
        Add graphics related params to the block.
        """
        x, y, w, h = 50, -40, 200, 150
        PORT_H, PORT_W = 10, 10

        QGraphicsRectItem.__init__(self, parent, scence)
        self.setRect(0, 0, w, h)
        self.setPos(x, y)

        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsPanel)
        self.setBrush(QBrush(QColor(200,200,200)))

        text = QGraphicsTextItem(self)
        text.setHtml('<b>Block Name</b><br />Dies ist ein Test, Dies ist ein Test, Dies ist ein Test')
        text.setTextWidth(w)

        # source port(s)
        num_sink_ports = 3
        self.souce_ports = []
        for i in range(num_sink_ports):
            y_port = (i + 0.5) * h / num_sink_ports - PORT_H / 2
            port = QGraphicsRectItem(self)
            port.setBrush(QColor(255,255,255))
            port.setRect(-PORT_W, y_port, PORT_W, PORT_H)
            port.setFlag(QGraphicsItem.ItemIsFocusable)
            self.souce_ports.append(port)

        # sink port(s)
        num_source_ports = 4
        self.sink_ports = []
        for i in range(num_source_ports):
            y_port = (i + 0.5) * h / num_source_ports - PORT_H / 2
            port = QGraphicsRectItem(self)
            port.setBrush(QColor(255,255,255))
            port.setPos(w, 0)
            port.setRect(0, y_port, PORT_W, PORT_H)
            port.setFlag(QGraphicsItem.ItemIsFocusable)

            self.sink_ports.append(port)


        print port.parentItem()

        #self.setG (Qt.ActionsContextMenu)
        #self.addActions((parent.main_window.menuEdit.actions()))

        Element.__init__(self)
        #self.init_extra()

    def init_extra(self):
        #add the position param
        self.get_params().append(self.get_parent().get_parent().Param(
            block=self,
            n=odict({
                'name': 'GUI Coordinate',
                'key': '_coordinate',
                'type': 'raw',
                'value': '(0, 0)',
                'hide': 'all',
            })
        ))
        self.get_params().append(self.get_parent().get_parent().Param(
            block=self,
            n=odict({
                'name': 'GUI Rotation',
                'key': '_rotation',
                'type': 'raw',
                'value': '0',
                'hide': 'all',
            })
        ))


    def contextMenuEvent(self, event):
        print event
        menu = QMenu()
        menu.addActions(self.parentWidget().main_window.menuEdit.actions())
        menu.show()
        event.accept()






    def get_coordinate(self):
        """
        Get the coordinate from the position param.

        Returns:
            the coordinate tuple (x, y) or (0, 0) if failure
        """
        #coor = eval(self.get_param('_coordinate').get_value())
        #x, y = map(int, coor)
        x, y = self.pos()
        return x, y


    def set_coordinate(self, coor):
        """
        Set the coordinate into the position param.

        Args:
            coor: the coordinate tuple (x, y)
        """
        #self.get_param('_coordinate').set_value(str(coor))
        self.setPos(*coor)

    def get_rotation(self):
        """
        Get the rotation from the position param.

        Returns:
            the rotation in degrees
        """
        return int(self.rotation())

    def set_rotation(self, rot):
        """
        Set the rotation into the position param.

        Args:
            rot: the rotation in degrees
        """
        #self.get_param('_rotation').set_value(str(rot))
        self.setRotation(rot)

    def create_shapes(self):
        """Update the block, parameters, and ports when a change occurs."""
        raise NotImplementedError

    def create_labels(self):
        """Create the labels for the signal block."""
        raise NotImplementedError

    def draw(self, gc, window):
        """
        Draw the signal block with label and inputs/outputs.

        Args:
            gc: the graphics context
            window: the gtk window to draw on
        """
        raise NotImplementedError
