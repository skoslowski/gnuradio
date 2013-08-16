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
""" Module to add new blocks """
import gtk
import sys
import os
from os.path import expanduser
from gnuradio import gr
import re
from ModtoolGRC import ModToolRemoveGRC, Errorbox
from Messages import project_folder_message


	
class RemoveBlockDialog(gtk.Dialog):
    
    def __init__(self):

        gtk.Dialog.__init__(self,
            title="Remove block",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )


        self.lib=False
        self.include=False
        self.swig=False
        self.python=False
        self.grc=False
        self.set_size_request(600, 400)
        vbox = gtk.VBox()
        self.vbox.pack_start(vbox, True, True, 0)

        self.path_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.path_hbox,False,False,10)
        self.path_hbox.show()

        self.path_l = gtk.Label("Choose block location (e.g. gr-howto)")
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

        self.block_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.block_name_hbox,False,False,10)
        self.block_name_hbox.show()

		
        self.block_name_l = gtk.Label("Enter block name")
        self.block_name_hbox.pack_start(self.block_name_l,False,False,10)	
        self.block_name_l.show()
        self.block_name_e = gtk.Entry()
        self.block_name_e.set_size_request(310,-1)
        self.block_name_hbox.pack_end(self.block_name_e,False)
        self.block_name_e.show()

        self.lib_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.lib_hbox,False,False,10)
        self.lib_hbox.show()

		
        self.lib_l = gtk.Label("Delete files from lib/?")
        self.lib_hbox.pack_start(self.lib_l,False,False,10)	
        self.lib_l.show()
        self.lib_e = gtk.Combo()
        self.lib_e.set_size_request(310,-1)
        self.lib_hbox.pack_end(self.lib_e,False)
        self.lib_e.entry.set_text("Yes")
        slist = ["Yes","No"]	
        self.lib_e.set_popdown_strings(slist)
        self.lib_e.show()

        self.include_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.include_hbox,False,False,10)
        self.include_hbox.show()

		
        self.include_l = gtk.Label("Delete files from include/?")
        self.include_hbox.pack_start(self.include_l,False,False,10)	
        self.include_l.show()
        self.include_e = gtk.Combo()
        self.include_e.set_size_request(310,-1)
        self.include_hbox.pack_end(self.include_e,False)
        self.include_e.entry.set_text("Yes")
        slist = ["Yes","No"]	
        self.include_e.set_popdown_strings(slist)
        self.include_e.show()

        self.swig_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.swig_hbox,False,False,10)
        self.swig_hbox.show()

		
        self.swig_l = gtk.Label("Delete files from swig/?")
        self.swig_hbox.pack_start(self.swig_l,False,False,10)	
        self.swig_l.show()
        self.swig_e = gtk.Combo()
        self.swig_e.set_size_request(310,-1)
        self.swig_hbox.pack_end(self.swig_e,False)
        self.swig_e.entry.set_text("Yes")
        slist = ["Yes","No"]	
        self.swig_e.set_popdown_strings(slist)
        self.swig_e.show()

        self.grc_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.grc_hbox,False,False,10)
        self.grc_hbox.show()

		
        self.grc_l = gtk.Label("Delete files from grc/?")
        self.grc_hbox.pack_start(self.grc_l,False,False,10)	
        self.grc_l.show()
        self.grc_e = gtk.Combo()
        self.grc_e.set_size_request(310,-1)
        self.grc_hbox.pack_end(self.grc_e,False)
        self.grc_e.entry.set_text("Yes")
        slist = ["Yes","No"]	
        self.grc_e.set_popdown_strings(slist)
        self.grc_e.show()

        self.python_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.python_hbox,False,False,10)
        self.python_hbox.show()

		
        self.python_l = gtk.Label("Delete files from python/?")
        self.python_hbox.pack_start(self.python_l,False,False,10)	
        self.python_l.show()
        self.python_e = gtk.Combo()
        self.python_e.set_size_request(310,-1)
        self.python_hbox.pack_end(self.python_e,False)
        self.python_e.entry.set_text("Yes")
        slist = ["Yes","No"]	
        self.python_e.set_popdown_strings(slist)
        self.python_e.show()
	
        self.show_all()



    def chooser_c(self,w):	
        self.fold_cr  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

		
        self.fold_cr.show()
        response = self.fold_cr.run()
        if response == gtk.RESPONSE_OK:
            self.new_f_name=self.fold_cr.get_filename()
            self.path_e.set_text(self.new_f_name)
            self.fold_cr.destroy()
        if response == gtk.RESPONSE_CANCEL:
            self.fold_cr.destroy()


    def run(self):

        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_OK:

            if self.lib_e.entry.get_text()=='Yes':
                self.lib=True
            if self.include_e.entry.get_text()=='Yes':
                self.include=True
            if self.swig_e.entry.get_text()=='Yes':
                self.swig=True
            if self.python_e.entry.get_text()=='Yes':
                self.python=True
            if self.grc_e.entry.get_text()=='Yes':
                self.grc=True
            try:
                fold_name=self.path_e.get_text().split('/')[-1]
                modname=fold_name.split('-')[1]
                if (fold_name.split('-')[0]=='gr'):
                    path=os.getcwd()
                    os.chdir(self.path_e.get_text())
                    rmblock=ModToolRemoveGRC(self.lib, self.include, self.swig, self.grc, self.python)
                    rmblock.setup(modname, self.block_name_e.get_text())
                    rmblock.run()
                    os.chdir(path)
                else:
                    Errorbox('No GNU Radio module found in the given directory. Quitting.')
            except IndexError:
                Errorbox('No GNU Radio module found in the given directory. Quitting.')
        elif response == gtk.RESPONSE_REJECT:
            pass
        self.destroy()
        return response == gtk.RESPONSE_OK
	

