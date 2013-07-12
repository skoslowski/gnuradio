"""
Copyright 2008, 2009, 2011 Free Software Foundation, Inc.
This file is part of GNU Radio

GNU Radio Companion is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

GNU Radio Companion is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

import os

from PyQt4.QtGui import *
from PyQt4 import QtCore
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

from . DrawingArea import DrawingArea
#from StateCache import StateCache


############################################################
## Notebook Page
############################################################

class EditorPage(QWidget):
    """A page in the notebook."""

    def __init__(self, main_window, flow_graph, file_path=''):
        """
        Page constructor.

        Args:
            main_window: main window
            file_path: path to a flow graph file
        """
        QWidget.__init__(self)

        self.main_window = main_window
        self._flow_graph = flow_graph

        self.set_proc(None)
        self.set_file_path(file_path)
        self.set_saved(True)

        #import the file
        initial_state = flow_graph.get_parent().parse_flow_graph(file_path)
        self.state_cache = None  # StateCache(initial_state)

        #import the data to the flow graph
        flow_graph.import_data(initial_state)

        #initialize page gui
        self.drawing_area = DrawingArea(self, flow_graph)
        layout = QHBoxLayout(self)
        layout.addWidget(self.drawing_area)
        layout.setMargin(0)

        self.get_flow_graph().populate_scene()
        #self.label = None
        #self.get_flow_graph().drawing_area = self.get_drawing_area()

    def get_drawing_area(self):
        return self.drawing_area

    def get_generator(self):
        """
        Get the generator object for this flow graph.

        Returns:
            generator
        """
        return self.get_flow_graph().get_parent().get_generator()(
            self.get_flow_graph(),
            self.get_file_path(),
        )

    def set_markup(self, markup):
        """
        Set the markup in this label.

        Args:
            markup: the new markup text
        """
        self.label.set_markup(markup)

    def get_proc(self):
        """
        Get the subprocess for the flow graph.

        Returns:
            the subprocess object
        """
        return self.process

    def set_proc(self, process):
        """
        Set the subprocess object.

        Args:
            process: the new subprocess
        """
        self.process = process

    def get_flow_graph(self):
        """
        Get the flow graph.

        Returns:
            the flow graph
        """
        return self._flow_graph

    def get_read_only(self):
        """
        Get the read-only state of the file.
        Always false for empty path.

        Returns:
            true for read-only
        """
        if not self.get_file_path(): return False
        return os.path.exists(self.get_file_path()) and \
        not os.access(self.get_file_path(), os.W_OK)

    def get_file_path(self):
        """
        Get the file path for the flow graph.

        Returns:
            the file path or ''
        """
        return self.file_path

    def set_file_path(self, file_path=''):
        """
        Set the file path, '' for no file path.

        Args:
            file_path: file path string
        """
        self.file_path = os.path.abspath(file_path) if file_path else ''

    def get_saved(self):
        """
        Get the saved status for the flow graph.

        Returns:
            true if saved
        """
        return self.saved

    def set_saved(self, saved=True):
        """
        Set the saved status.

        Args:
            saved: boolean status
        """
        self.saved = saved

    def get_state_cache(self):
        """
        Get the state cache for the flow graph.

        Returns:
            the state cache
        """
        return self.state_cache
