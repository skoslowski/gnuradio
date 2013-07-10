import os
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

from . Block import Block
from . Constants import NEW_FLOGRAPH_TITLE
from . EditorPage import EditorPage
from . BlockLibrary import BlockLibrary
import Messages

from ui_MainWindow import Ui_MainWindow



class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, platform=None):
        QMainWindow.__init__(self)

        self._platform = platform
        self.setupUi(self)

        self.blockLibrary = BlockLibrary(self, platform, self.get_flow_graph)
        self.addDockWidget(Qt.RightDockWidgetArea, self.blockLibrary)

        self.actionLibrary.triggered.connect(self.blockLibrary.show)
        self.actionNew.triggered.connect(self.new_page)
        self.actionClose.triggered.connect(self.close_page)
        self.editorTabs.tabCloseRequested.connect(self.close_page)
        self.actionPaste.triggered.connect(self.new_block)

        # self.btwin = BlockTreeWindow(platform, self.get_flow_graph)

        self.reportDock.close()

        self.new_page()

        self.new_block()

        # ToDo: Load UI Prefs
        #load preferences and show the main window
		#Preferences.load(platform)
		#self.resize(*Preferences.main_window_size())
		#self.flow_graph_vpaned.set_position(Preferences.reports_window_position())
		#self.hpaned.set_position(Preferences.blocks_window_position())
		#self.show_all()

    def new_page(self, file_path='', show=False):
        """
        Create a new notebook page.
        Set the tab to be selected.

        Args:
        file_path: optional file to load into the flow graph
        show: true if the page should be shown after loading
        """
        #if the file is already open, show the open page and return
        if file_path and file_path in self._get_files(): #already open
            page = self.editorTabs.children()[self._get_files().index(file_path)]
            self._set_page(page)
            return

        try: #try to load from file
            if file_path:
                Messages.send_start_load(file_path)

            flow_graph = None # self._platform.get_new_flow_graph()
            #flow_graph.grc_file_path = file_path

            page = EditorPage(
                self,
                flow_graph=flow_graph,
                file_path=file_path,
            )

            if file_path:
                Messages.send_end_load()

        except Exception as e: #return on failure
            Messages.send_fail_load(e)
            if isinstance(e, KeyError) and str(e) == "'options'":
                # This error is unrecoverable, so crash gracefully
                exit(-1)
                return

        else:
            #add this page to the notebook
            self.editorTabs.addTab(page, NEW_FLOGRAPH_TITLE)

            #only show if blank or manual
            if not file_path or show:
                self.editorTabs.setCurrentWidget(page)

    def close_pages(self):
        """
        Close all the pages in this notebook.

        Returns:
            true if all closed
        """
        open_files = filter(lambda f: f, self._get_files()) #filter blank files
        open_file = self.get_page().get_file_path()
        #close each page
        for page in self._iter_pages():
            self.close_page(page)
        if self.notebook.count():
            return False
        #save state before closing
        # Todo: Save state
        #Preferences.files_open(open_files)
        #Preferences.file_open(open_file)
        #Preferences.main_window_size(self.get_size())
        #Preferences.reports_window_position(self.flow_graph_vpaned.get_position())
        #Preferences.blocks_window_position(self.hpaned.get_position())
        #Preferences.save()
        return True

    def close_page(self, index=None):
        """
        Close the current page.
        If the notebook becomes empty, and ensure is true,
        call new page upon exit to ensure that at least one page exists.

        Args:
            index: int
        """
        if index is None:
            index = self.editorTabs.currentIndex()
        page_to_be_closed = self.editorTabs.widget(index)
        #show the page if it has an executing flow graph or is unsaved
        if page_to_be_closed.get_proc() or not page_to_be_closed.get_saved():
            self._set_page(self.page_to_be_closed)

        #unsaved? ask the user
        if not page_to_be_closed.get_saved() and self._save_changes():
            #Actions.FLOW_GRAPH_SAVE() #try to save
            if not page_to_be_closed.get_saved(): #still unsaved?
                return
        #stop the flow graph if executing
        #if self.page_to_be_closed.get_proc():
        #    Actions.FLOW_GRAPH_KILL()
        #remove the page
        self.editorTabs.removeTab(index)


    def new_block(self):
        graphicScene = self.get_page().get_drawing_area().scene()
        block = Block()
        graphicScene.addItem(block)


    ############################################################
    # Misc
    ############################################################

    def update(self):
        """
        Set the title of the main window.
        Set the titles on the page tabs.
        Show/hide the tab bar window.
        """
        current_page = self.get_page()
        self.setWindowTitle("{saved}{base}{ro}{dir}{platform}".format(
            saved='*' if current_page.get_saved() else '',
            base=os.path.basename(current_page.get_file_path()),
            ro=' (read only)' if current_page.read_only() else '',
            dir=os.path.dirname(current_page.get_file_path()),
            platform=self._platform.get_name()
        ))
        #ToDO: set tab titles

        #show/hide notebook tabs
        self.editorTabs.tabBar().setVisible(self.editorTabs.count() > 1)

    def get_page(self):
        """
        Get the selected page.

        Returns:
            the selected page
        """
        return self.editorTabs.currentWidget()

    def get_flow_graph(self):
        """
        Get the selected flow graph.

        Returns:
            the selected flow graph
        """
        return self.get_page().get_flow_graph()

    def get_focus_flag(self):
        """
        Get the focus flag from the current page.

        Returns:
            the focus flag
        """
        raise NotImplementedError


    ############################################################
    # Helpers
    ############################################################

    def _set_page(self, page):
        """
        Set the current page.

        Args:
            page: the page widget
        """
        self.current_page = page
        self.editorTabs.setCurrentWidget(page)

    def _save_changes(self):
        """
        Save changes to flow graph?

        Returns:
            true if yes
        """
        return QMessageBox.question(self, 'Unsaved Changes!',
                             'Would you like to save changes before closing?',
                             QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes

    def _get_files(self):
        """
        Get the file names for all the pages, in order.

        Returns:
            list of file paths
        """
        return map(lambda page: page.get_file_path(), self._get_pages())

    def _iter_pages(self):
        """
        Iterate over all pages in the notebook.
        """
        for i in range(self.editorTabs.count()):
            yield self.editorTabs.widget(i)




