import os

from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

from . Block import Block
from . Constants import NEW_FLOGRAPH_TITLE
from . EditorPage import EditorPage
from . BlockLibrary import BlockLibrary
import Messages
import Preferences

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

        self.reportDock.close()

        #load preferences and show the main window
        Preferences.load(platform)
        # ToDo: use QSettings?
        state = Preferences.main_window_state()
        if state is not None: self.restoreState(state)
        geometry = Preferences.main_window_geometry()
        if geometry is not None: self.restoreGeometry(geometry)

    ############################################################
    # Report Window
    ############################################################

    def add_report_line(self, line):
        """
        Place line at the end of the text buffer, then scroll its window all the way down.

        Args:
            line: the new text
        """
        self.reportText.append(line)

        #ToDo: fix scroll down
        scrollbar = self.reportText.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        #scrollbar.triggerAction(QAbstractSlider.SliderToMaximum)

    ############################################################
    # Pages: create and close
    ############################################################

    def new_page(self, file_path='', show=False):
        """
        Create a new notebook page.
        Set the tab to be selected.

        Args:
        file_path: optional file to load into the flow graph
        show: true if the page should be shown after loading
        """
        #if the file is already open, show the open page and return
        if file_path:
            for page in self._iter_pages():
                if page.file_path == file_path:
                    self.editorTabs.setCurrentWidget(page)
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


        self.new_block()

    def close_pages(self):
        """
        Close all the pages in this notebook.

        Returns:
            true if all closed
        """
        open_files = (page.get_file_path() for page in self._iter_pages())
        open_files = filter(lambda f: f, open_files) #filter blank files
        open_file = self.get_page().get_file_path()

        #close each page
        for page in self._iter_pages():
            self.close_page(page)
        if self.editorTabs.count():
            return False

        #save state before closing
        Preferences.files_open(open_files)
        Preferences.file_open(open_file)
        return True

    def close_page(self, page=None):
        """
        Close the current page.
        If the notebook becomes empty, and ensure is true,
        call new page upon exit to ensure that at least one page exists.

        Args:
            index: int
        """
        page = page or self.get_page()
        #show the page if it has an executing flow graph or is unsaved
        if page.get_proc() or not page.get_saved():
            self.editorTabs.setCurrentWidget(page)

        #unsaved? ask the user
        if not page.get_saved() and self._save_changes():
            #Actions.FLOW_GRAPH_SAVE() #try to save
            if not page.get_saved(): #still unsaved?
                return
        #stop the flow graph if executing
        #if page.get_proc():
        #    Actions.FLOW_GRAPH_KILL()

        #remove the page
        self.editorTabs.removeTab(self.editorTabs.indexOf(page))


    def new_block(self):
        graphicScene = self.get_page().get_drawing_area().scene()
        block = Block()
        graphicScene.addItem(block)


    ############################################################
    # Misc
    ############################################################

    def closeEvent(self, event):
        Preferences.main_window_state(self.saveState())
        Preferences.main_window_geometry(self.saveGeometry())
        Preferences.save()
        if self.close_pages():
            event.accept()

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

    ############################################################
    # Helpers
    ############################################################

    def _save_changes(self):
        """
        Save changes to flow graph?

        Returns:
            true if yes
        """
        return QMessageBox.question(self, 'Unsaved Changes!',
                             'Would you like to save changes before closing?',
                             QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes

    def _iter_pages(self):
        """
        Iterate over all pages in the notebook.
        """
        for i in range(self.editorTabs.count()):
            yield self.editorTabs.widget(i)




