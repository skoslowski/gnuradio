from PyQt5 import QtCore, QtGui, QtWidgets

class MainView(QtWidgets.QMainWindow):
    '''
    Class that handles the main view definition for the main grc window
    '''

    def __init__(self):
        ''' 
        Initialize the main window and call wrappers to initialize subviews
        '''
        QtWidgets.QMainWindow.__init__(self)

        self.setObjectName("main")
        self.resize(1024, 860)

        ### TODO: Not sure about document mode
        self.setDocumentMode(True)

        self.setDockOptions(QtWidgets.QMainWindow.AllowNestedDocks | \
            QtWidgets.QMainWindow.AllowTabbedDocks | \
            QtWidgets.QMainWindow.AnimatedDocks)


        ### TODO: Also need to pull from the saved preferences as what to show and where

        # Generate the rest of the window
        self.init_actions()
        self.init_menus()
        self.init_toolbars()
        self.init_statusbars()
        self.init_other()

        self.retranslateUi()
        self.actionQuit.triggered.connect(self.close)
        #self.actionReport.triggered.connect(self.reportDock.show)
        QtCore.QMetaObject.connectSlotsByName(self)

    ### TODO: Move to resources folder as list
    def init_actions(self):
        self.actionNew = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("document-new")
        self.actionNew.setIcon(icon)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("document-open")
        self.actionOpen.setIcon(icon)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("document-save")
        self.actionSave.setIcon(icon)
        self.actionSave.setObjectName("actionSave")
        self.actionSave_As = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("document-save-as")
        self.actionSave_As.setIcon(icon)
        self.actionSave_As.setObjectName("actionSave_As")
        self.actionClose = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("document-close")
        self.actionClose.setIcon(icon)
        self.actionClose.setObjectName("actionClose")
        self.actionQuit = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("application-exit")
        self.actionQuit.setIcon(icon)
        self.actionQuit.setObjectName("actionQuit")
        self.actionUndo = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("edit-undo")
        self.actionUndo.setIcon(icon)
        self.actionUndo.setObjectName("actionUndo")
        self.actionRedo = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("edit-redo")
        self.actionRedo.setIcon(icon)
        self.actionRedo.setObjectName("actionRedo")
        self.actionCut = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("edit-cut")
        self.actionCut.setIcon(icon)
        self.actionCut.setObjectName("actionCut")
        self.actionCopy = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("edit-copy")
        self.actionCopy.setIcon(icon)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("edit-paste")
        self.actionPaste.setIcon(icon)
        self.actionPaste.setObjectName("actionPaste")
        self.actionDelete = QtWidgets.QAction(self)
        icon = QtGui.QIcon.fromTheme("edit-delete")
        self.actionDelete.setIcon(icon)
        self.actionDelete.setObjectName("actionDelete")
        self.actionGenerate = QtWidgets.QAction(self)
        self.actionGenerate.setObjectName("actionGenerate")
        self.actionExecute = QtWidgets.QAction(self)
        self.actionExecute.setObjectName("actionExecute")
        self.actionKill = QtWidgets.QAction(self)
        self.actionKill.setObjectName("actionKill")
        self.actionHelp = QtWidgets.QAction(self)
        self.actionHelp.setObjectName("actionHelp")
        self.actionTypes = QtWidgets.QAction(self)
        self.actionTypes.setObjectName("actionTypes")
        self.actionAbout = QtWidgets.QAction(self)
        self.actionAbout.setObjectName("actionAbout")
        self.actionLibrary = QtWidgets.QAction(self)
        self.actionLibrary.setObjectName("actionLibrary")
        self.actionReport = QtWidgets.QAction(self)
        self.actionReport.setObjectName("actionReport")
        self.actionRotateLeft = QtWidgets.QAction(self)
        self.actionRotateLeft.setObjectName("actionRotateLeft")
        self.actionRotateRight = QtWidgets.QAction(self)
        self.actionRotateRight.setObjectName("actionRotateRight")
        self.actionEnable = QtWidgets.QAction(self)
        self.actionEnable.setObjectName("actionEnable")
        self.actionDisable = QtWidgets.QAction(self)
        self.actionDisable.setObjectName("actionDisable")
        self.actionProperties = QtWidgets.QAction(self)
        self.actionProperties.setObjectName("actionProperties")
        self.actionFileToolbar = QtWidgets.QAction(self)
        self.actionFileToolbar.setObjectName("actionFileToolbar")
        self.actionEditToolbar = QtWidgets.QAction(self)
        self.actionEditToolbar.setObjectName("actionEditToolbar")
        self.actionRunToolbar = QtWidgets.QAction(self)
        self.actionRunToolbar.setObjectName("actionRunToolbar")

    def init_menus(self):
        '''
        Define the main menubar for the application.
        '''
        menubar = QtWidgets.QMenuBar(self)
        menubar.setObjectName("menu")

        menuFile = QtWidgets.QMenu(menubar)
        menuFile.setObjectName("menu::file")

        menuEdit = QtWidgets.QMenu(menubar)
        menuEdit.setObjectName("menu::edit")

        menuView = QtWidgets.QMenu(menubar)
        menuView.setObjectName("menu::view")

        menuBuild = QtWidgets.QMenu(menubar)
        menuBuild.setObjectName("menu::build")

        menuHelp = QtWidgets.QMenu(menubar)
        menuHelp.setObjectName("menu::help")

        
        menuFile.addAction(self.actionNew)
        menuFile.addAction(self.actionOpen)
        menuFile.addSeparator()
        menuFile.addAction(self.actionSave)
        menuFile.addAction(self.actionSave_As)
        menuFile.addSeparator()
        menuFile.addAction(self.actionClose)
        menuFile.addAction(self.actionQuit)
        self.menuFile = menuFile

        menuEdit.addAction(self.actionUndo)
        menuEdit.addAction(self.actionRedo)
        menuEdit.addSeparator()
        menuEdit.addAction(self.actionCut)
        menuEdit.addAction(self.actionCopy)
        menuEdit.addAction(self.actionPaste)
        menuEdit.addAction(self.actionDelete)
        menuEdit.addSeparator()
        menuEdit.addAction(self.actionRotateLeft)
        menuEdit.addAction(self.actionRotateRight)
        menuEdit.addAction(self.actionEnable)
        menuEdit.addAction(self.actionDisable)
        menuEdit.addSeparator()
        menuEdit.addAction(self.actionProperties)
        self.menuEdit = menuEdit

        menuView.addAction(self.actionLibrary)
        menuView.addAction(self.actionReport)
        self.menuView = menuView

        menuBuild.addAction(self.actionGenerate)
        menuBuild.addAction(self.actionExecute)
        menuBuild.addAction(self.actionKill)
        self.menuBuild = menuBuild

        menuHelp.addAction(self.actionHelp)
        menuHelp.addAction(self.actionTypes)
        menuHelp.addSeparator()
        menuHelp.addAction(self.actionAbout)
        self.menuHelp = menuHelp

        menubar.addAction(self.menuFile.menuAction())
        menubar.addAction(self.menuEdit.menuAction())
        menubar.addAction(self.menuView.menuAction())
        menubar.addAction(self.menuBuild.menuAction())
        menubar.addAction(self.menuHelp.menuAction())

        # Set the main window's menu bar
        self.menubar = menubar
        self.setMenuBar(menubar)

    def init_toolbars(self):
        self.fileToolbar = QtWidgets.QToolBar(self)
        self.fileToolbar.setObjectName("fileToolbar")
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.fileToolbar)

        self.editToolbar = QtWidgets.QToolBar(self)
        self.editToolbar.setObjectName("editToolbar")
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.editToolbar)

        self.runToolbar = QtWidgets.QToolBar(self)
        self.runToolbar.setObjectName("runToolbar")
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.runToolbar)

        self.fileToolbar.addAction(self.actionNew)
        self.fileToolbar.addAction(self.actionOpen)
        self.fileToolbar.addAction(self.actionSave)
        self.fileToolbar.addAction(self.actionClose)
        self.editToolbar.addAction(self.actionCut)
        self.editToolbar.addAction(self.actionCopy)
        self.editToolbar.addAction(self.actionPaste)
        self.editToolbar.addAction(self.actionDelete)
        self.runToolbar.addAction(self.actionGenerate)
        self.runToolbar.addAction(self.actionExecute)
        self.runToolbar.addAction(self.actionKill)

    def init_statusbars(self):
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

    def init_other(self):

        centralwidget = QtWidgets.QWidget(self)
        centralwidget.setObjectName("main::central")

        layout = QtWidgets.QHBoxLayout(centralwidget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setObjectName("main::central::layout")

        tabs = QtWidgets.QTabWidget(centralwidget)
        tabs.setObjectName("main::central::layout::tabs")

        #tab_1 = QtWidgets.QWidget()
        #tab_1.setObjectName("tab_3")
        
        #tab_2 = QtWidgets.QWidget()
        #tab_2.setObjectName("tab_4")

        #tab_layout = QtWidgets.QHBoxLayout()
        #layout.setSpacing(0)
        #layout.setContentsMargins(0, 0, 0, 0)
        #layout.setObjectName("main::central::layout")

        #tabs.addTab(tab_1, "")
        #tabs.addTab(tab_2, "")

        #layout_5 = QtWidgets.QHBoxLayout()
        #layout_5.setObjectName("horizontalLayout_5" 
  
        #self.horizontalLayout_5.addWidget(self.editorTabs)
        #self.horizontalLayout.addLayout(self.horizontalLayout_5)
  
        self.setCentralWidget(centralwidget)

    ### TODO: Move action list and translations out of view
    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("self", "GNU Radio Companion"))
        #self.editorTabs.setTabText(self.editorTabs.indexOf(self.tab_3), _translate("self", "Tab 1"))
        #self.editorTabs.setTabText(self.editorTabs.indexOf(self.tab_4), _translate("self", "Tab 2"))
        self.menuFile.setTitle(_translate("self", "File"))
        self.menuEdit.setTitle(_translate("self", "Edit"))
        self.menuView.setTitle(_translate("self", "View"))
        self.menuBuild.setTitle(_translate("self", "Build"))
        self.menuHelp.setTitle(_translate("self", "Help"))
        self.fileToolbar.setWindowTitle(_translate("self", "File Toolbar"))
        #self.reportDock.setWindowTitle(_translate("self", "Console"))
        self.editToolbar.setWindowTitle(_translate("self", "Edit Toolbar"))
        self.runToolbar.setWindowTitle(_translate("self", "Run Toolbar"))
        #self.dockWidget.setWindowTitle(_translate("self", "Project"))
        self.actionNew.setText(_translate("self", "New"))
        self.actionNew.setToolTip(_translate("self", "New Flowgraph"))
        self.actionNew.setShortcut(_translate("self", "Ctrl+N"))
        self.actionOpen.setText(_translate("self", "Open"))
        self.actionOpen.setShortcut(_translate("self", "Ctrl+O"))
        self.actionSave.setText(_translate("self", "Save"))
        self.actionSave.setShortcut(_translate("self", "Ctrl+S"))
        self.actionSave_As.setText(_translate("self", "Save As"))
        self.actionSave_As.setShortcut(_translate("self", "Ctrl+Shift+S"))
        self.actionClose.setText(_translate("self", "Close"))
        self.actionClose.setShortcut(_translate("self", "Ctrl+W"))
        self.actionQuit.setText(_translate("self", "Quit"))
        self.actionUndo.setText(_translate("self", "Undo"))
        self.actionUndo.setShortcut(_translate("self", "Ctrl+Z"))
        self.actionRedo.setText(_translate("self", "Redo"))
        self.actionRedo.setShortcut(_translate("self", "Ctrl+Y"))
        self.actionCut.setText(_translate("self", "Cut"))
        self.actionCut.setShortcut(_translate("self", "Ctrl+X"))
        self.actionCopy.setText(_translate("self", "Copy"))
        self.actionCopy.setShortcut(_translate("self", "Ctrl+C"))
        self.actionPaste.setText(_translate("self", "Paste"))
        self.actionPaste.setShortcut(_translate("self", "Ctrl+V"))
        self.actionDelete.setText(_translate("self", "Delete"))
        self.actionDelete.setShortcut(_translate("self", "Del"))
        self.actionGenerate.setText(_translate("self", "Generate"))
        self.actionGenerate.setShortcut(_translate("self", "F5"))
        self.actionExecute.setText(_translate("self", "Execute"))
        self.actionExecute.setShortcut(_translate("self", "F6"))
        self.actionKill.setText(_translate("self", "Kill"))
        self.actionKill.setShortcut(_translate("self", "F7"))
        self.actionHelp.setText(_translate("self", "Help"))
        self.actionHelp.setShortcut(_translate("self", "F1"))
        self.actionTypes.setText(_translate("self", "Types"))
        self.actionAbout.setText(_translate("self", "About"))
        self.actionLibrary.setText(_translate("self", "Library"))
        self.actionLibrary.setShortcut(_translate("self", "Ctrl+L"))
        self.actionReport.setText(_translate("self", "Report"))
        self.actionRotateLeft.setText(_translate("self", "Rotate Left"))
        self.actionRotateRight.setText(_translate("self", "Rotate Right"))
        self.actionEnable.setText(_translate("self", "Enable"))
        self.actionDisable.setText(_translate("self", "Disable"))
        self.actionProperties.setText(_translate("self", "Properties"))
        self.actionFileToolbar.setText(_translate("self", "File"))
        self.actionEditToolbar.setText(_translate("self", "Edit"))
        self.actionRunToolbar.setText(_translate("self", "Run"))

