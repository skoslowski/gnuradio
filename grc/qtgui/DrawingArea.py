from PyQt4.QtGui import *
from PyQt4.QtCore import Qt


class DrawingArea(QGraphicsView):
    def __init__(self, parent, flow_graph):
        QGraphicsView.__init__(self, parent)
        self._flow_graph = flow_graph

        self.setFrameShape(QFrame.NoFrame)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setAcceptDrops(True)
        self.setScene(QGraphicsScene())

        #ToDo: Better put this in Block()
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.addActions(parent.main_window.menuEdit.actions())

    def get_focus_flag(self):
        #ToDo: Why do we need this?
        return False

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            factor = 1.2
            if event.delta() < 0 :
                factor = 1.0 / factor
            self.scale(factor, factor)
        else:
            QGraphicsView.wheelEvent(self, event)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        print event.mimeData().text()

