class BlockTreeController(object):
    def __init__(self):

        # Load the main view class and initialize QMainWindow
        self._window = main.MainView()
        self._platform = None

        # Also load and initialize child controllers
        #report_view = reports.ReportView()
        #self.report_controller = ReportContoller(report_view)
        #self._window.addDockWidget(QtCore.Qt.DockWidgetArea(8), report_view)

        #block_view = blocktree.BlockTreeView()
        #self._window.addDockWidget(QtCore.Qt.RightDockWidgetArea, block_view)

        #project_view = projects.ProjectView()
        #self._window.addDockWidget(QtCore.Qt.RightDockWidgetArea, project_view)

        #self.actionLibrary.triggered.connect(self.blockLibrary.show)
        #self.actionNew.triggered.connect(self.new_page)
        #self.actionClose.triggered.connect(self.close_page)
        #self.editorTabs.tabCloseRequested.connect(self.close_page)

        #self.reportDock.close()

        #load preferences and show the main window
        #Preferences.load(platform)
        # ToDo: use QSettings?
        #state = Preferences.main_window_state()
        #if state is not None: self.restoreState(state)
        #geometry = Preferences.main_window_geometry()
        #if geometry is not None: self.restoreGeometry(geometry)
