import os

from PyQt5 import QtCore, QtGui, QtWidgets

from . import views
from . import controllers

class MainController(object):
    def __init__(self):

        # Load the main view class and initialize QMainWindow
        self._window = views.MainView()
        self._platform = None

        # Also load and initialize child controllers
        report_view = views.ReportsView()
        self.report_controller = controllers.ReportsController(report_view)
        self._window.addDockWidget(QtCore.Qt.DockWidgetArea(8), report_view)

        self.projects_controller = controllers.ProjectsController()
        self._window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.projects_controller.get_view())



        self.report_controller.add_line("s")

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

    def start(self):
        self._window.show()

    def set_icon(self, path):
        icon = QtGui.QIcon(path)
        self._window.setWindowIcon(icon)

    ############################################################
    # Report Window
    ############################################################

    def add_report_line(self, line):
        pass

    ############################################################
    # Pages: create and close
    ############################################################

    def new_page(self, file_path='', show=False):
        pass

    def close_pages(self):
        pass

    def close_page(self, index=None):
        pass
    ############################################################
    # Misc
    ############################################################

    def closeEvent(self, event):
        pass

    def update(self):
        pass

    def get_page(self):
        pass

    def get_flow_graph(self):
        pass

    ############################################################
    # Helpers
    ############################################################

    def _save_changes(self):
       pass



