#! /usr/bin/env python3
# standard modules
import sys

# third-party modules
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

# custom modules
from flowgraph    import FlowGraph
from blocklibrary import BlockLibrary

class GrcAppWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(GrcAppWindow, self).__init__()
        
        self.setWindowTitle('GRC')
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        self.flowgraph = FlowGraph(self, 'data/rx_logo.grc')
        self.setCentralWidget(self.flowgraph)
        self.addDockWidget(Qt.LeftDockWidgetArea, BlockLibrary())

    def createActions(self):
        style = self.style()
        qs = QtWidgets.QStyle
        icon_src = style.standardIcon
        icon = icon_src(qs.SP_DirIcon)
        icon_theme = QtGui.QIcon.fromTheme
        # ## File Actions ## #
        self.newAct = QtWidgets.QAction(icon_theme("document-new"), 
                      "&New", self, 
                      shortcut=QtGui.QKeySequence.New,
                      statusTip="Create a new flow graph", 
                      triggered=self.newFile)
        
        self.openAct = QtWidgets.QAction(icon_theme("document-open"),
                       "&Open...", self, 
                       shortcut=QtGui.QKeySequence.Open,
                       statusTip="Open an existing flow graph", 
                       triggered=self.open)
        
        self.saveAct = QtWidgets.QAction(icon_theme("document-save"),
                       "&Save", self, 
                       shortcut=QtGui.QKeySequence.Save,
                       statusTip="Save the current flow graph", 
                       triggered=self.save)
        
        self.saveAsAct = QtWidgets.QAction("Save &As...", self, 
                         shortcut=QtGui.QKeySequence.SaveAs,
                         statusTip="Save the flow graph under a new name",
                         triggered=self.saveAs)
                         
        self.printAct = QtWidgets.QAction(icon_theme('document-print'),
                         "&Print...", self, 
                         shortcut=QtGui.QKeySequence.Print,
                         statusTip="Print the current flow graph",
                         triggered=self.app_print)
                         
        self.screenCaptureAct = QtWidgets.QAction("Screen Capture", self, 
                         statusTip="Create a screen capture of the current flow graph",
                         triggered=self.screenCapture)
                         
        self.closeAct = QtWidgets.QAction(icon_src(qs.SP_DialogCancelButton), 
                        "Close", self, 
                        shortcut=QtGui.QKeySequence.Close,
                        statusTip="Close the current flow graph",
                        triggered=self.close)
                         
        self.exitAct = QtWidgets.QAction("E&xit", self, shortcut="Ctrl+Q",
                       statusTip="Exit the application", triggered=self.close)
                       
        # ## Edit Actions ## #
        self.undoAct = QtWidgets.QAction(icon_theme('edit-undo'), "Undo",
                      self, shortcut=QtGui.QKeySequence.Undo,
                      statusTip="",
                      triggered=self.undo)
                      
        self.redoAct = QtWidgets.QAction(QtGui.QIcon.fromTheme('edit-redo'), "Redo",
                      self, shortcut=QtGui.QKeySequence.Redo,
                      statusTip="",
                      triggered=self.redo)
                      
        self.cutAct = QtWidgets.QAction(QtGui.QIcon.fromTheme('edit-cut'), "Cu&t",
                      self, shortcut=QtGui.QKeySequence.Cut,
                      statusTip="Cut the current selection's contents to the clipboard",
                      triggered=self.cut)
                      
        self.copyAct = QtWidgets.QAction(QtGui.QIcon.fromTheme('edit-copy'),
                      "&Copy", self, shortcut=QtGui.QKeySequence.Copy,
                      statusTip="Copy the current selection's contents to the clipboard",
                      triggered=self.copy)
                      
        self.pasteAct = QtWidgets.QAction(QtGui.QIcon.fromTheme('edit-paste'),
                        "&Paste", self, shortcut=QtGui.QKeySequence.Paste,
                        statusTip="Paste the clipboard's contents into the current selection",
                        triggered=self.paste)

        self.deleteAct = QtWidgets.QAction(QtGui.QIcon.fromTheme('edit-delete'),
                         "&Delete", self, shortcut=QtGui.QKeySequence.Delete,
                         statusTip="Delete the selected blocks",
                         triggered=self.delete)
                        
        self.rotateCcwAct = QtWidgets.QAction(icon_src(qs.SP_ArrowLeft),
                            "Rotate Counterclockwise", self, shortcut=QtGui.QKeySequence.MoveToPreviousChar,
                            statusTip="Rotate the selected block 90 degress counterclockwise",
                            triggered=self.rotateCcw)

        self.rotateCwAct = QtWidgets.QAction(icon_src(qs.SP_ArrowRight),
                           "Rotate Counterclockwise", self, shortcut=QtGui.QKeySequence.MoveToNextChar,
                           statusTip="Rotate the selected block 90 degress clockwise",
                           triggered=self.rotateCw)
                       
        # ## View Actions ## #
        self.errorsAct = QtWidgets.QAction(QtGui.QIcon.fromTheme('errors'),
                         "&Errors", self, shortcut='E',
                         statusTip="View the flowgraph errors",
                         triggered=self.errors)
                        
        self.findBlockAct = QtWidgets.QAction(QtGui.QIcon.fromTheme('edit-find'),
                            "&Find Block", self, shortcut=QtGui.QKeySequence.Find,
                            statusTip="Search for a block by name (and key)",
                            triggered=self.findBlock)
                        
        # ## Help Actions ## #
        self.aboutAct = QtWidgets.QAction("&About", self,
                        statusTip="Show the application's About box",
                        triggered=self.about)
                        
        # Disable some actions, by default                  
        self.saveAct.setEnabled(False)
        
        self.undoAct.setEnabled(False)
        self.redoAct.setEnabled(False)
        self.cutAct.setEnabled(False)
        self.copyAct.setEnabled(False)
        self.pasteAct.setEnabled(False)
        self.deleteAct.setEnabled(False)
        self.rotateCcwAct.setEnabled(False)
        self.rotateCwAct.setEnabled(False)
        
        self.errorsAct.setEnabled(False)
        
    def createMenus(self):
        self.createFileMenu()
        self.createEditMenu()
        self.createViewMenu()
        self.createBuildMenu()
        self.createHelpMenu()
        
    def createFileMenu(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator();
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addSeparator();
        self.fileMenu.addAction(self.screenCaptureAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator();
        self.fileMenu.addAction(self.closeAct)
        self.fileMenu.addAction(self.exitAct)
        
    def createEditMenu(self):
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addSeparator();
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)
        self.editMenu.addAction(self.deleteAct)
        self.editMenu.addSeparator();
        self.editMenu.addAction(self.rotateCcwAct)
        self.editMenu.addAction(self.rotateCwAct)
        
        self.menuBar().addSeparator()
        
    def createViewMenu(self):
        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.errorsAct)
        self.viewMenu.addAction(self.findBlockAct)
        
    def createBuildMenu(self):
        self.buildMenu = self.menuBar().addMenu("&Build")
        
    def createHelpMenu(self):
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        
    def createToolBars(self):
        self.fileToolBar = self.addToolBar("File")
        self.fileToolBar.addAction(self.newAct)
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addAction(self.saveAct)
        self.fileToolBar.addAction(self.closeAct)
        self.fileToolBar.addAction(self.printAct)
        
        self.editToolBar = self.addToolBar("Edit")
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyAct)
        self.editToolBar.addAction(self.pasteAct)    
        self.editToolBar.addAction(self.deleteAct)    
        self.editToolBar.addSeparator()    
        self.editToolBar.addAction(self.rotateCcwAct)    
        self.editToolBar.addAction(self.rotateCwAct)    
        
    def createStatusBar(self):
         self.statusBar().showMessage("Ready")


    # ## action handlers ## #
    
    def newFile(self):
        print ('new file')

    def open(self):
        print ('open')
        filename, filtr = QtGui.QFileDialog.getOpenFileName(self, 
                          self.openAct.statusTip(),
                          filter='Flow Graph Files (*.grc);;All files (*.*)')
        if filename:
            self.flowgraph = FlowGraph(self, filename)
        
    def save(self):
        print ('save')
        
    def saveAs(self):
        print ('saveAs')
        
    def app_print(self):
        print ('print')
        
    def screenCapture(self):
        print ('screen capture')
        
    def close(self):
        print ('close')
           
    def undo(self):
        print ('undo')
        
    def redo(self):
        print ('redo')
        
    def cut(self):
        print ('cut')
        
    def copy(self):
        print ('copy')
        
    def paste(self):
        print ('paste')
        
    def delete(self):
        print ('delete')
        
    def rotateCcw(self):
        print ('rotate ccw')
        
    def rotateCw(self):
        print ('rotate cw')
               
    def errors(self):
        print ('errors')
        
    def findBlock(self):
        print ('find block')
        
    def about(self):
        QtGui.QMessageBox.about(self, "GNU Radio Companion", "<b>GNU Radio Companion</b>")
    
if __name__ == '__main__':
    import sys
    app  = QtWidgets.QApplication(sys.argv)
    dw   = QtWidgets.QDesktopWidget()
    ds   = dw.availableGeometry()
    main = GrcAppWindow()
    main.resize(ds.width() * 0.7, ds.height() * 0.7)
    main.show()
    sys.exit(app.exec_())

