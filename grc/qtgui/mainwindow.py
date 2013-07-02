from PyQt4.QtGui import *

from PyQt4 import QtCore

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

from ui_MainWindow import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, platform=None):
        QMainWindow.__init__(self)

        self.setupUi(self)

        self.actionNew.triggered.connect(self.new_page)
        self.actionClose.triggered.connect(self.close_page)
        self.editorTabs.tabCloseRequested.connect(self.close_page)

        self.consoleDock.close()

        new = QTreeWidgetItem()
        new.setText(0, "Test")
        self.blockTree.insertTopLevelItem(0, new)

        new2 = QTreeWidgetItem()
        new2.setText(0, "Test2")
        new.addChild(new2)

        # ToDo: Load UI Prefs


    def new_page(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        graphicsView = QGraphicsView(tab)

        layout.addWidget(graphicsView)
        layout.setMargin(0)

        graphicsView.setFrameShape(QFrame.NoFrame)

        self.editorTabs.addTab(tab, _fromUtf8("New*"))
        self.editorTabs.setCurrentWidget(tab)

    def close_page(self, index=None):
        if index is None:
            index = self.editorTabs.currentIndex()
        self.editorTabs.removeTab(index)