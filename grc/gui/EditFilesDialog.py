#
# Copyright 2013 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
""" Module to edit files in project folder """
import gtk
import sys
import os
from os.path import expanduser
from gnuradio import gr
import re
from subprocess import Popen, PIPE
from ModtoolGRC import Errorbox
from Preferences import get_editor, add_OOT_editors

	
class EditFilesDialog(gtk.Dialog):

    """
    A dialog to edit the files related to module blocks.
    """
    
    def __init__(self):

        """
        dialog contructor.
        """
        gtk.Dialog.__init__(self,
            title="Edit files",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )



        self.set_size_request(600, 150)
        vbox = gtk.VBox()
        self.vbox.pack_start(vbox, True, True, 0)

        #choose editor path.
        self.editor_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.editor_hbox,False,False,7)
        self.editor_hbox.show()

        self.editor_label = gtk.Label("Choose your editor's path")
        self.editor_hbox.pack_start(self.editor_label,False)	
        self.editor_label.show()
        self.enter_but = gtk.Button("...")
        self.editor_hbox.pack_end(self.enter_but,False)
        self.enter_but.set_size_request(70,-1)
        self.enter_but.connect("pressed", self.choose_path,)
        self.enter_but.show()
        self.editor_entity = gtk.Entry()
        self.editor_entity.set_size_request(250,-1)
        self.editor_hbox.pack_start(self.editor_entity,True)
        self.editor_entity.show()
        self.show_all()
	

    def executable_filter(self, filter_info, data):

        '''
        Filter to choose executable files.
        '''
        path = filter_info[0]
        return os.access(path, os.X_OK)


    def choose_path(self,w):

        '''
        choose the path to editor.
        '''	
        self.file_path_name  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

        filter_file = gtk.FileFilter()
        filter_file.set_name("executable files")
        filter_file.add_custom(gtk.FILE_FILTER_FILENAME, self.executable_filter, None)
        self.file_path_name.add_filter(filter_file)
        self.file_path_name.show()
        response = self.file_path_name.run()
        if response == gtk.RESPONSE_OK:
            self.new_f_name=self.file_path_name.get_filename()
            self.editor_entity.set_text(self.new_f_name)
            self.file_path_name.destroy()

        if response == gtk.RESPONSE_CANCEL:
            self.file_path_name.destroy()

		

    def run(self):

        """
        Run the dialog and get its response.
        
        Returns:
            true if the response was accept
        """

        run_again=True
        #dialog box remains open even if error message is displayed.
        while run_again:
            response = gtk.Dialog.run(self)
            if response == gtk.RESPONSE_OK:			
                if os.path.exists(self.editor_entity.get_text()):
                    editor=self.editor_entity.get_text()
                    add_OOT_editors(editor)
                    run_again=False
                else:
                    Errorbox('File not found')
            elif response == gtk.RESPONSE_REJECT:
                run_again=False
            else:
                self.destroy()
                return response == gtk.RESPONSE_OK
        self.destroy()
        return response == gtk.RESPONSE_OK



def editor_path():
    global editor
    try:
        if editor:
            return editor
    except NameError:
        return None


