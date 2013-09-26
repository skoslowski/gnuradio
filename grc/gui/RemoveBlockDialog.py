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
""" Module to remove blocks """
import gtk
import sys
import os
from os.path import expanduser
from gnuradio import gr
import re
from ModtoolGRC import ModToolRemoveGRC, Errorbox
from Messages import OTM_message
from Preferences import get_OOT_module, add_OOT_module

	
class RemoveBlockDialog(gtk.Dialog):

    """
    A dialog to remove blocks from out of tree module.
    """
    
    def __init__(self):

        """
        dialog contructor.
        """
        gtk.Dialog.__init__(self,
            title="Remove block",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )

        self.set_size_request(500, 170)
        vbox = gtk.VBox()
        self.vbox.pack_start(vbox, True, True, 0)

        #choose module name.
        self.module_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.module_hbox,False,False,7)
        self.module_hbox.show()

        self.mod_path=''
        self.module_label = gtk.Label("Choose block location")
        self.module_hbox.pack_start(self.module_label,False)	
        self.module_label.show()
        self.module_entry = gtk.combo_box_new_text()
        self.module_label.set_size_request(250,-1)
        self.module_hbox.pack_start(self.module_entry,True)
        #create a drop down list of five recently used modules.
        self.mod_list=['mod1','mod2','mod3','mod4','mod5']
        check=False
        for i in self.mod_list:
            if get_OOT_module(i) is not None:
                self.module_entry.append_text(get_OOT_module(i).split('/')[-1])
                check=True
        if check is False:
            self.module_entry.append_text("No active module")
        #choose some other module.
        self.module_entry.append_text("Select some other module")
        self.module_entry.set_active(0)
        #get module location from /.grc config file using module name.	
        for i in self.mod_list:
            model = self.module_entry.get_model()
            index = self.module_entry.get_active()
            name = model[index][0]
            if get_OOT_module(i) is not None:
                if name == get_OOT_module(i).split('/')[-1]:
                    self.mod_path=get_OOT_module(i)
                    break
        self.module_entry.connect('changed', self.handle_change)
        self.module_entry.show()	

	#create an entry box to choose block name.
        self.block_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.block_hbox,False,False,7)
        self.block_hbox.show()

        self.block_label = gtk.Label("Select block name")
        self.block_hbox.pack_start(self.block_label,False)	
        self.block_label.show()
        #create a drop down list of all blocks present in a selected module.
        self.block_entry = gtk.combo_box_new_text()
        self.block_label.set_size_request(250,-1)
        self.block_hbox.pack_start(self.block_entry,True)
        self.block_list=self.get_blk_list(self.mod_path)
        if not self.block_list:
            self.block_entry.set_sensitive(False)
        else:
            for i in self.block_list:
                self.block_entry.append_text(i)
            self.block_entry.set_active(0)
            self.active_block=self.block_entry.get_model()[self.block_entry.get_active()][0]	

        self.block_entry.show()
		

	
        self.show_all()

    def get_blk_list(self,path):

        """
        get a list of blocks present in selected module.
        """

        blk_lst=[]
        mod_name=path.split('/')[-1].split('-')[-1]
        if os.path.isdir(path):
            for dirs, subdirs, files in os.walk(path):
                for f in files:
                    if re.search(".xml\Z", f) and dirs==path+'/grc':
                        blk_name=f.split('.')[0].split('_')[-1]
                        if blk_name not in blk_lst:
                            blk_lst.append(blk_name)
                    if re.search("_impl.cc\Z", f) and dirs==path+'/lib':
                        blk_name=f.split('.')[0].split('_')[0]
                        if blk_name not in blk_lst:
                            blk_lst.append(blk_name)
                    if re.search(".h\Z", f) and 'api' not in f.lower() and 'qa' not in f.lower() and 'impl' not in f.lower() and  dirs==path+'/'+mod_name+'/include':
                        blk_name=f.split('.')[0]
                        if blk_name not in blk_lst:
                            blk_lst.append(blk_name)
                    if re.search(".py\Z", f) and dirs.split('/')[-1]=='python' and 'init' not in f.lower()  and dirs==path+'/python':
                        blk_name=f.split('.')[0]
                        if blk_name not in blk_lst:
                            blk_lst.append(blk_name)
        return blk_lst


    def handle_change(self, module_entry):

        """
        any change in module selection will update the /.grc config file.
        file chooser dialog can also be opened to choose some other module.
        get a list of blocks present in selected module.
        """


        model = self.module_entry.get_model()
        index = self.module_entry.get_active()
        name = model[index][0]
        #open file chooser dialog
        if name=="Select some other module":
            self.mod  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

	    self.mod.set_current_folder(os.path.expanduser('~'))
            self.mod.show()
            response = self.mod.run()
            if response == gtk.RESPONSE_OK:
                self.mod_path=self.mod.get_filename()
                self.module_entry.append_text(self.mod_path.split('/')[-1])
                self.module_entry.set_active(index+1)
                #set the choosen module as currently active module in /.grc config file
                add_OOT_module(self.mod_path)
                self.mod.destroy()
            if response == gtk.RESPONSE_CANCEL:
                self.mod.destroy()
        #set the choosen module as currently active module in /.grc config file
        else:
            for i in self.mod_list:
                if get_OOT_module(i) is not None:
                    if name == get_OOT_module(i).split('/')[-1]:
                        self.mod_path=get_OOT_module(i)
                        add_OOT_module(self.mod_path)
                        break
        no_of_blks=len(self.block_list)
        self.block_list=self.get_blk_list(self.mod_path)
        print self.block_list
        #display block list.
        if not self.block_list:
            self.block_entry.set_sensitive(False)
        else:
            self.block_entry.set_sensitive(True)
            for i in range(0,no_of_blks):
                self.block_entry.remove_text(no_of_blks-1-i)
            for i in self.block_list:
                self.block_entry.append_text(i)
            self.block_entry.set_active(0)
            self.active_block=self.block_entry.get_active_text()


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
                try:
                    fold_name=self.mod_path.split('/')[-1]
                    modname=fold_name.split('-')[1]
                    if (fold_name.split('-')[0]=='gr'):
                        #borrowed version of ModToolRemove for GRC.
                        rmblock=ModToolRemoveGRC(modname, self.block_entry.get_active_text(),self.mod_path)
                        rmblock.setup()
                        rmblock.run()
                        OTM_message('Deleting all the occurences of block "%s" from "gr-%s". \n' %(self.block_entry.get_active_text(),modname))
                        run_again=False
                    else:
                        Errorbox('No GNU Radio module found in the given directory. Quitting.')
                except IndexError:
                    Errorbox('No GNU Radio module found in the given directory. Quitting.')
            elif response == gtk.RESPONSE_REJECT:
                run_again=False
            else:
                self.destroy()
                return response == gtk.RESPONSE_OK
        self.destroy()
        return response == gtk.RESPONSE_OK
	

