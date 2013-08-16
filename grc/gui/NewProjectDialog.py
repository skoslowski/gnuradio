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
""" Module to create project folder """
import gtk
import sys
import os
from gnuradio import gr
from os.path import expanduser
import re
from MainWindow import MainWindow
from .. base import ParseXML
from subprocess import Popen, PIPE
from ModtoolGRC import ModToolNewModuleGRC
from Messages import project_folder_message

class NewProjectDialog(gtk.Dialog):

    def __init__(self,win):

        gtk.Dialog.__init__(self,
            title="Create new project folder",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )
        self.dir_path=''
        self.path_e=''
        self.main_window = win
        self.set_size_request(550, 170)
        vbox = gtk.VBox()
        self.vbox.pack_start(vbox, True, True, 0)

        self.fname_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.fname_hbox,False,False,10)
        self.fname_hbox.show()

		
        self.fname_l = gtk.Label("Enter folder/module name")
        self.fname_hbox.pack_start(self.fname_l,False,False,10)	
        self.fname_l.show()
        self.fname_e = gtk.Entry()
        self.fname_e.set_size_request(310,-1)
        self.fname_e.connect('changed', self.changed_folder)
        self.fname_hbox.pack_end(self.fname_e,False)
        self.fname_e.show()

        self.path_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.path_hbox,False,False,10)
        self.path_hbox.show()

        self.path_l = gtk.Label("Choose folder location")
        self.path_hbox.pack_start(self.path_l,False,False,10)	
        self.path_l.show()
        self.enter_but = gtk.Button("...")
        self.path_hbox.pack_end(self.enter_but,False)
        self.enter_but.set_size_request(110,-1)
        self.enter_but.connect("pressed", self.chooser_c,)
        self.enter_but.show()
        self.path_e = gtk.Entry()
        self.path_e.set_size_request(200,-1)
        self.path_hbox.pack_end(self.path_e,False)
        self.path_e.show()
        self.show_all()

    def changed_folder(self, fname_e):
        try: 
            if not self.path_e.get_text()=='':
                self.path_e.set_text(self.path_e.get_text().replace(self.path_e.get_text().split('/')[-1],'gr-%s'%self.fname_e.get_text()))
        except NameError:
            pass

    def chooser_c(self,w):	
        self.fold_path_name  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

		
        self.fold_path_name.show()
        response = self.fold_path_name.run()
        if response == gtk.RESPONSE_OK:
            self.dir_path=self.fold_path_name.get_filename()
            self.path_e.set_text('%s/gr-%s' % (self.dir_path,self.fname_e.get_text()))
            self.fold_path_name.destroy()
        if response == gtk.RESPONSE_CANCEL:
            self.fold_path_name.destroy()




    def run(self):

        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_OK:
            newmod=ModToolNewModuleGRC()
            if newmod.setup(self.fname_e.get_text(),self.dir_path) is True:
                newmod.run()
                project_folder_message('\nout of tree module has been created in %s\n\n' % self.path_e.get_text())
                build_path='%s/build' % (self.path_e.get_text())
                Popen(['mkdir',build_path])
                file_path='%s/apps/main.grc' %(self.path_e.get_text())
                self.main_window.new_page()
                self.main_window.get_page().set_file_path(file_path)
                ParseXML.to_file(self.main_window.get_flow_graph().export_data(), self.main_window.get_page().get_file_path());
                self.main_window.get_flow_graph().grc_file_path = '/%s' % self.main_window.get_page().get_file_path()
                self.main_window.get_page().set_saved(True)
        elif response == gtk.RESPONSE_REJECT:
            pass
        self.destroy()
        return response == gtk.RESPONSE_OK


	

    

