import sys
from threading import Thread

from PyQt4.QtGui import QApplication

import Messages
from . MainWindow import MainWindow

class ActionHandler:
    """
    The action handler will setup all the major window components,
    and handle button presses and flow graph operations from the GUI.
    """

    def __init__(self, file_paths, platform):
        """
        ActionHandler constructor.
        Create the main window, setup the message handler, import the preferences,
        and connect all of the action handlers. Finally, enter the gtk main loop and block.

        Args:
        file_paths: a list of flow graph file passed from command line
        platform: platform module
        """
        self.clipboard = None
        self.platform = platform

        #setup the main window
        app = QApplication([])
        self.main_window = MainWindow(platform)
        self.main_window.actionRotateLeft.triggered.connect(self._rotate_left_action)
        self.main_window.actionRotateRight.triggered.connect(self._rotate_right_action)

        #setup the messages
        #Messages.register_messenger(self.main_window.add_report_line)
        #Messages.send_init(platform)

        self.init_file_paths = file_paths

        self.main_window.show()
        sys.exit(app.exec_())


    def _handle_key_press(self, widget, event):
        pass

    def _quit(self, window, event):
        pass

    def _rotate_left_action(self, ccw=True):
        current_page = self.main_window.get_page()
        if current_page:
            for item in current_page.get_drawing_area().scene().selectedItems():
                item.rotate(90 if ccw else -90)

    def _rotate_right_action(self):
        self._rotate_left_action(False)


class ExecFlowGraphThread(Thread):
    """Execute the flow graph as a new process and wait on it to finish."""

    def __init__ (self, action_handler):
        """
        ExecFlowGraphThread constructor.

        Args:
        action_handler: an instance of an ActionHandler
        """
        Thread.__init__(self)
        self.update_exec_stop = action_handler.update_exec_stop
        self.flow_graph = action_handler.get_flow_graph()
        #store page and dont use main window calls in run
        self.page = action_handler.get_page()
        Messages.send_start_exec(self.page.get_generator().get_file_path())
        #get the popen
        try:
            self.p = self.page.get_generator().get_popen()
            self.page.set_proc(self.p)
            #update
            self.update_exec_stop()
            self.start()
        except Exception as e:
            Messages.send_verbose_exec(str(e))
            Messages.send_end_exec()

    def run(self):
        """
        Wait on the executing process by reading from its stdout.
        Use gobject.idle_add when calling functions that modify gtk objects.
        """
        #handle completion
        #r = "\n"
        #while(r):
        #	gobject.idle_add(Messages.send_verbose_exec, r)
        #	r = os.read(self.p.stdout.fileno(), 1024)
        #gobject.idle_add(self.done)

    def done(self):
        """Perform end of execution tasks."""
        Messages.send_end_exec()
        self.page.set_proc(None)
        self.update_exec_stop()