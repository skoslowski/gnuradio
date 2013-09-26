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
# Boston, MA 0217-1301, USA.
#
""" Module to create out of tree module/project folder """
import gtk
import sys
import os
from gnuradio import gr
from os.path import expanduser
import re
from MainWindow import MainWindow
from .. base import ParseXML
from subprocess import Popen, PIPE
from ModtoolGRC import ModToolNewModuleGRC, ModToolException
from Messages import OTM_message
from Preferences import add_OOT_module

class NewModuleDialog(gtk.Dialog):

    """
    A dialog to create an out of tree module.
    """

    def __init__(self,main_window):

        """
        dialog contructor.
        
        Args:
            main_window: a main window instance
        """

        gtk.Dialog.__init__(self,
            title="Create new module",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )
        self.dir_path=''
        self.main_window = main_window
        self.set_size_request(600, 170)
        vbox = gtk.VBox()
        self.vbox.pack_start(vbox, True, True, 0)

	#create an entry box to enter module name.
        self.module_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.module_hbox,False,False,7)
        self.module_hbox.show()
 	
        self.module_label = gtk.Label("Enter module name")
        self.module_hbox.pack_start(self.module_label,False)	
        self.module_label.show()
        self.module_entry = gtk.Entry()
        self.module_label.set_size_request(250,-1)
        self.module_entry.connect('changed', self.handle_change)
        self.module_hbox.pack_start(self.module_entry,True)
        self.module_entry.show()

        #create an entry box to choose module/folder location.
        self.path_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.path_hbox,False,False,7)
        self.path_hbox.show()

        self.path_label = gtk.Label("Choose folder location")
        self.path_hbox.pack_start(self.path_label,False)	
        self.path_label.show()
        self.enter_but = gtk.Button("...")
        self.path_hbox.pack_end(self.enter_but,False)
        self.enter_but.set_size_request(70,-1)
        self.enter_but.connect("pressed", self.choose_folder,)
        self.enter_but.show()
        self.path_entry = gtk.Entry()
        self.path_label.set_size_request(250,-1)
        self.path_entry.connect('changed', self.update_location)
        self.path_hbox.pack_start(self.path_entry,True)
        self.path_entry.show()
        self.show_all()

    def handle_change(self, module_entry):
        """
        Any change in module name will update the location of module accordingly.
        """
        try: 
            if self.path_entry.get_text():
                #update in module location if module name is changed after selecting the module location.
                if 'gr-' in self.path_entry.get_text().split('/')[-1].lower():
                    self.path_entry.set_text(self.path_entry.get_text().replace(self.path_entry.get_text().split('/')[-1],'gr-%s'%self.module_entry.get_text()))
                #update in module location if module name is entered after selecting the module location.
                else:
                    self.path_entry.set_text('%s/gr-%s'%(self.path_entry.get_text(), self.module_entry.get_text()))
        except NameError:
            pass

    def update_location(self, path_entry):
        """
        In case of manual entry for modulae location, module name appends automatically.
        """
        if not self.module_entry.get_text()=='' and 'gr-' not in self.path_entry.get_text().split('/')[-1].lower():
            self.path_entry.set_text(self.path_entry.get_text()+'/gr-%s'%self.module_entry.get_text())

    def choose_folder(self,w):
        """
        create a file chooser dialog to select a location for new out of tree module.
        """        	
        self.fold_path_name  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
        #set home folder as default folder.
        self.fold_path_name.set_current_folder(os.path.expanduser('~'))
        self.fold_path_name.show()
        response = self.fold_path_name.run()
        if response == gtk.RESPONSE_OK:
            self.dir_path=self.fold_path_name.get_filename()
            if self.module_entry.get_text():
                self.path_entry.set_text('%s/gr-%s' % (self.dir_path,self.module_entry.get_text()))
            else:
                self.path_entry.set_text(self.dir_path)
            self.fold_path_name.destroy()
        if response == gtk.RESPONSE_CANCEL:
            self.fold_path_name.destroy()




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
                #borrowed version of ModToolNewModule for GRC. 
                newmod=ModToolNewModuleGRC()
                if not self.dir_path:
                    self.dir_path=self.path_entry.get_text().replace(self.path_entry.get_text().split('/')[-1],'')
                try:
                    newmod.setup(self.module_entry.get_text(),self.dir_path)
                    newmod.run()
                    #add module location in /.grc config file to use it as an active module.
                    add_OOT_module(self.path_entry.get_text())
                    OTM_message('Out of tree module has been created in "%s".\n' % self.path_entry.get_text())
                    #create build dir
                    build_path='%s/build' % (self.path_entry.get_text())
                    Popen(['mkdir',build_path])
                    #create a flowgraph in /apps dir.
                    file_path='%s/apps/main.grc' %(self.path_entry.get_text())
                    self.main_window.new_page()
                    self.main_window.get_page().set_file_path(file_path)
                    ParseXML.to_file(self.main_window.get_flow_graph().export_data(), self.main_window.get_page().get_file_path());
                    self.main_window.get_flow_graph().grc_file_path = '/%s' % self.main_window.get_page().get_file_path()
                    self.main_window.get_page().set_saved(True)
                    run_again=False
                except ModToolException:
                    pass
            elif response == gtk.RESPONSE_REJECT:
                run_again=False
            else:
                self.destroy()
                return response == gtk.RESPONSE_OK
        self.destroy()
        return response == gtk.RESPONSE_OK


	

    

