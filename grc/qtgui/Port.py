from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

class Port(QGraphicsRectItem):

    def __init__(self, parent=None, scence=None):
        """
        Port contructor.
        Add graphics related params to the block.
        """
        PORT_H, PORT_W = 10, 10

        QGraphicsRectItem.__init__(self, parent, scence)
        self.setRect(-PORT_W, y_port, PORT_W, PORT_H)
        self.setPos(x, y)

        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsPanel)
        self.setBrush(QColor(255,255,255))
