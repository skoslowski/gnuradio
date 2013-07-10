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
        QGraphicsRectItem.__init__(self, 10, 10, 200, 200, parent, scence)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsPanel)
        self.setBrush(QBrush(QColor(200,200,200)))

        text = QGraphicsTextItem(self)
        text.setHtml('<b>Block Name</b><br />Dies ist ein Test, Dies ist ein Test, Dies ist ein Test')
        text.setTextWidth(200)
        text.setPos(10,10)

        #self.setContextMenuPolicy(Qt.ActionsContextMenu)
        #self.addActions(parent.main_window.menuEdit.actions())

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
