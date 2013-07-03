from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

class FlowGraph(QGraphicsView):
    def __init__(self, parent = None):
        QGraphicsView.__init__(self, parent)
        self.parent = parent

        self.setFrameShape(QFrame.NoFrame)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setScene(QGraphicsScene())

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            factor = 1.2
            if event.delta() < 0 :
                factor = 1.0 / factor
            self.scale(factor, factor)
        else:
            QGraphicsView.wheelEvent(self, event)