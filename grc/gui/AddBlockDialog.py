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
from ModtoolGRC import ModToolAddGRC, Errorbox
import re
from Messages import project_folder_message


	
class AddBlockDialog(gtk.Dialog):
    


    def __init__(self):

        gtk.Dialog.__init__(self,
            title="Add new block",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )



        self.set_size_request(600, 350)
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

        self.type_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.type_name_hbox,False,False,10)
        self.type_name_hbox.show()

		
        self.type_name_l = gtk.Label("Enter block type")
        self.type_name_hbox.pack_start(self.type_name_l,False,False,10)	
        self.type_name_l.show()
        self.type_name_e = gtk.Combo()
        self.type_name_e.set_size_request(310,-1)
        self.type_name_hbox.pack_end(self.type_name_e,False)
        self.type_name_e.entry.set_text("general")
        slist = [ "general","sink", "source", "sync", "decimator", "interpolator","tagged_stream", "hier", "noblock"]	
        self.type_name_e.set_popdown_strings(slist)
        self.type_name_e.show()

        self.arg_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.arg_name_hbox,False,False,10)
        self.arg_name_hbox.show()

		
        self.arg_name_l = gtk.Label("Enter args")
        self.arg_name_hbox.pack_start(self.arg_name_l,False,False,10)	
        self.arg_name_l.show()
        self.arg_name_e = gtk.Entry()
        self.arg_name_e.set_size_request(310,-1)
        self.arg_name_hbox.pack_end(self.arg_name_e,False)
        self.arg_name_e.show()
	
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
            try:
                fold_name=self.path_e.get_text().split('/')[-1]
                modname=fold_name.split('-')[1]
                if fold_name.split('-')[0]=='gr':
                    if os.path.isdir(self.path_e.get_text()):
                        path=os.getcwd()
                        os.chdir(self.path_e.get_text())
                        addblock=ModToolAddGRC()
                        if addblock.setup(modname, self.type_name_e.entry.get_text(), self.block_name_e.get_text(), self.arg_name_e.get_text()) is True:
                            addblock.run()
                            project_folder_message('\nBlock %s has been added in %s\n\n' % (self.block_name_e.get_text(), self.path_e.get_text()))
                        os.chdir(path)
                    else:
                        Errorbox('%s is not found'% self.path_e.get_text())
                else:
                    Errorbox('No GNU Radio module found in the given directory. Quitting.')
            except IndexError:
                Errorbox('No GNU Radio module found in the given directory. Quitting.')
        elif response == gtk.RESPONSE_REJECT:
            pass
        self.destroy()
        return response == gtk.RESPONSE_OK

	

