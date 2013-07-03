from PyQt4.QtGui import *


class Block(QGraphicsRectItem):

    def __init__(self, parent=None, scence=None):
        QGraphicsRectItem.__init__(self, 10, 10,200,200, parent, scence)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsPanel)
        self.setBrush(QBrush(QColor(200,200,200)))

        text = QGraphicsTextItem(self)
        text.setHtml('<b>Block Name</b><br />Dies ist ein Test, Dies ist ein Test, Dies ist ein Test')
        text.setTextWidth(200)
        text.setPos(10,10)