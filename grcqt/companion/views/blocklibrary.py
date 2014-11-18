#! /usr/bin/env python3

# third-party modules
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt

class BlockLibrary(QtWidgets.QDockWidget):
    def __init__(self):
        super(BlockLibrary, self).__init__()


if __name__ == '__main__':
    import sys
                           
    app  = QtWidgets.QApplication(sys.argv)
    main = QtWidgets.QMainWindow()
    main.setCentralWidget(QtWidgets.QWidget())
    main.addDockWidget(Qt.LeftDockWidgetArea, BlockLibrary())
    main.show()
    sys.exit(app.exec_())

