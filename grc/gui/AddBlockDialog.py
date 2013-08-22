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
""" Module to add new blocks """
import gtk
import sys
import os
from os.path import expanduser
from gnuradio import gr
from ModtoolGRC import ModToolAddGRC, Errorbox
import re
from Messages import project_folder_message
from Preferences import get_OOT_module, add_OOT_module

	
class AddBlockDialog(gtk.Dialog):
    


    def __init__(self):

        gtk.Dialog.__init__(self,
            title="Add new block",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )



        self.set_size_request(600, 300)
        vbox = gtk.VBox()
        self.vbox.pack_start(vbox, True, True, 0)
       

        self.mod_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.mod_hbox,False,False,7)
        self.mod_hbox.show()

        self.mod_path=''
        self.mod_name_l = gtk.Label("Choose block location (e.g. gr-howto)")
        self.mod_hbox.pack_start(self.mod_name_l,False,False,7)	
        self.mod_name_l.show()
        self.mod_name_e = gtk.combo_box_new_text()
        self.mod_name_e.set_size_request(310,-1)
        self.mod_hbox.pack_end(self.mod_name_e,False)
        self.mod_list=['mod1','mod2','mod3','mod4','mod5']
        check=False
        for i in self.mod_list:
            if get_OOT_module(i) is not None:
                self.mod_name_e.append_text(get_OOT_module(i).split('/')[-1])
                check=True
        if check is False:
            self.mod_name_e.append_text("No active module")
        self.mod_name_e.append_text("Select some module")
        self.mod_name_e.set_active(0)	
        for i in self.mod_list:
            model = self.mod_name_e.get_model()
            index = self.mod_name_e.get_active()
            name = model[index][0]
            if get_OOT_module(i) is not None:
                if name == get_OOT_module(i).split('/')[-1]:
                    self.mod_path=get_OOT_module(i)
                    break
        self.mod_name_e.connect('changed', self.changed_folder)
        self.mod_name_e.show()

        self.block_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.block_name_hbox,False,False,7)
        self.block_name_hbox.show()

		
        self.block_name_l = gtk.Label("Enter block name")
        self.block_name_hbox.pack_start(self.block_name_l,False,False,7)	
        self.block_name_l.show()
        self.block_name_e = gtk.Entry()
        self.block_name_e.set_size_request(310,-1)
        self.block_name_hbox.pack_end(self.block_name_e,False)
        self.block_name_e.show()

        self.type_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.type_name_hbox,False,False,7)
        self.type_name_hbox.show()

		
        self.type_name_l = gtk.Label("Enter block type")
        self.type_name_hbox.pack_start(self.type_name_l,False,False,7)	
        self.type_name_l.show()
        self.type_name_e = gtk.Combo()
        self.type_name_e.set_size_request(310,-1)
        self.type_name_hbox.pack_end(self.type_name_e,False)
        self.type_name_e.entry.set_text("general")
        slist = [ "general","sink", "source", "sync", "decimator", "interpolator","tagged_stream", "hier", "noblock"]	
        self.type_name_e.set_popdown_strings(slist)
        self.type_name_e.show()

        self.arg_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.arg_name_hbox,False,False,7)
        self.arg_name_hbox.show()

		
        self.arg_name_l = gtk.Label("Enter args")
        self.arg_name_hbox.pack_start(self.arg_name_l,False,False,7)	
        self.arg_name_l.show()
        self.arg_name_e = gtk.Entry()
        self.arg_name_e.set_size_request(310,-1)
        self.arg_name_hbox.pack_end(self.arg_name_e,False)
        self.arg_name_e.show()
	
        self.show_all()

    def changed_folder(self, mod_name_e):
        model = self.mod_name_e.get_model()
        index = self.mod_name_e.get_active()
        name = model[index][0]
        if name=="Select some module":
            self.mod  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

	    self.mod.set_current_folder(os.path.expanduser('~'))
            self.mod.show()
            response = self.mod.run()
            if response == gtk.RESPONSE_OK:
                self.mod_path=self.mod.get_filename()
                self.mod_name_e.append_text(self.mod_path.split('/')[-1])
                self.mod_name_e.set_active(index+1)
                add_OOT_module(self.mod_path)
                self.mod.destroy()
            if response == gtk.RESPONSE_CANCEL:
                self.mod.destroy()
        else:
            for i in self.mod_list:
                if get_OOT_module(i) is not None:
                    if name == get_OOT_module(i).split('/')[-1]:
                        self.mod_path=get_OOT_module(i)
                        add_OOT_module(self.mod_path)
                        break


    def run(self):

        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_OK:
            try:
                fold_name=self.mod_path.split('/')[-1]
                modname=fold_name.split('-')[1]
                if fold_name.split('-')[0]=='gr':
                    if os.path.isdir(self.mod_path):
                        addblock=ModToolAddGRC(self.mod_path,modname, self.type_name_e.entry.get_text(), self.block_name_e.get_text(), self.arg_name_e.get_text())
                        if addblock.setup() is True:
                            addblock.run()
                            project_folder_message('Block "%s" has been added in "%s".\n' % (self.block_name_e.get_text(), self.mod_path))
                    else:
                        Errorbox('%s is not found'% self.mod_path)
                else:
                    Errorbox('No GNU Radio module found in the given directory. Quitting.')
            except IndexError:
                Errorbox('No GNU Radio module found in the given directory. Quitting.')
        elif response == gtk.RESPONSE_REJECT:
            pass
        self.destroy()
        return response == gtk.RESPONSE_OK

	

