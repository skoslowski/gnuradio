from PyQt5 import QtCore, QtGui, QtWidgets

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class BlockTreeView(QtWidgets.QDockWidget):
    '''
    Block library view
    '''

    def __init__(self):
        QtWidgets.QDockWidget.__init__(self)
        self.setObjectName("blocktree")
        
        self.resize(400, 300)
        self.setFloating(False)

        contents = QtWidgets.QWidget()
        contents.setObjectName("blocktree::contents")

        layout = QtWidgets.QVBoxLayout(contents)
        layout.setSpacing(0)
        #layout.setMargin(0)
        layout.setObjectName("blocktree::contents::layout")

        blocktree = QtWidgets.QTreeWidget(contents)
        blocktree.setDragEnabled(True)
        blocktree.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        blocktree.setColumnCount(1)
        blocktree.setObjectName("blocktree::contents::blocktree")
        blocktree.header().setVisible(False)
        self.blocktree = blocktree

        layout.addWidget(blocktree)
        self.setWidget(contents)

        self.retranslate()

    def retranslate(self):
        #self.setWindowTitle(_translate("blockLibraryDock", "Library", None))
        #self.blockTree.headerItem().setText(0, _translate("blockLibraryDock", "Blocks", None))
        self.setWindowTitle("Block Tree") 
        self.blocktree.headerItem().setText(0, "Blocks")
