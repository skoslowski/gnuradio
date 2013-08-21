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
from Preferences import get_OOT_module, add_OOT_module

	
class RemoveBlockDialog(gtk.Dialog):
    
    def __init__(self):

        gtk.Dialog.__init__(self,
            title="Remove block",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )


        self.lib=False
        self.include=False
        self.swig=True
        self.python=True
        self.grc=False
        self.grc_fold=False
        self.lib_fold=False
        self.include_fold=False
        self.set_size_request(600, 320)
        vbox = gtk.VBox()
        self.vbox.pack_start(vbox, True, True, 0)

        self.mod_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.mod_hbox,False,False,10)
        self.mod_hbox.show()

        self.mod_path=''
        self.mod_name_l = gtk.Label("Choose block location (e.g. gr-howto)")
        self.mod_hbox.pack_start(self.mod_name_l,False,False,10)	
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
        vbox.pack_start(self.block_name_hbox,False,False,10)
        self.block_name_hbox.show()

        self.block_name_l = gtk.Label("Select block name")
        self.block_name_hbox.pack_start(self.block_name_l,False,False,10)	
        self.block_name_l.show()
        self.block_name_e = gtk.combo_box_new_text()
        self.block_name_e.set_size_request(310,-1)
        self.block_name_hbox.pack_end(self.block_name_e,False)
        self.block_list=self.get_blk_list(self.mod_path)
        if not self.block_list:
            self.block_name_e.set_sensitive(False)
        else:
            for i in self.block_list:
                self.block_name_e.append_text(i)
            self.block_name_e.set_active(0)
            self.active_block=self.block_name_e.get_model()[self.block_name_e.get_active()][0]
            self.files_info(self.mod_path,self.active_block)	



        self.block_name_e.connect('changed', self.choose_block)
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
        if not self.block_list or self.lib_fold is False:
            self.lib_e.set_sensitive(False)
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
        if not self.block_list or self.include_fold is False:
            self.include_e.set_sensitive(False)
        self.include_e.show()

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
        if not self.block_list or self.grc_fold is False:
            self.grc_e.set_sensitive(False)
        self.grc_e.show()


        '''self.swig_hbox = gtk.HBox(gtk.FALSE,0)
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
        if self.check is False:
            self.swig_e.set_sensitive(False)
        self.swig_e.show()


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
        if self.check is False:
            self.python_e.set_sensitive(False)
        self.python_e.show()'''
	
        self.show_all()

    def get_blk_list(self,path):
        blk_lst=[]
        if os.path.isdir(path):
            for dirs, subdirs, files in os.walk(path):
                for f in files:
                    if re.search(".xml\Z", f):
                        blk_name=f.split('.')[0].split('_')[-1]
                        if blk_name not in blk_lst:
                            blk_lst.append(blk_name)
                    if re.search("_impl.cc\Z", f):
                        blk_name=f.split('.')[0].split('_')[0]
                        if blk_name not in blk_lst:
                            blk_lst.append(blk_name)
                    if re.search(".h\Z", f) and 'api' not in f.lower() and 'qa' not in f.lower() and 'impl' not in f.lower():
                        blk_name=f.split('.')[0]
                        if blk_name not in blk_lst:
                            blk_lst.append(blk_name)
        return blk_lst

    def files_info(self,path,blk):
        self.grc_fold=False
        self.lib_fold=False
        self.include_fold=False
        if os.path.isdir(path):
            for dirs, subdirs, files in os.walk(path):
                for f in files:
                    if re.search(blk+".xml\Z", f):
                        self.grc_fold=True
                    if re.search(blk+"_impl.cc\Z", f):
                        self.lib_fold=True
                    if re.search(blk+".h\Z", f) and 'api' not in f.lower() and 'qa' not in f.lower():
                        self.include_fold=True


    def choose_block(self, block_name_e):
        
        self.active_block=self.block_name_e.get_active_text()
        if self.active_block is not None:
            self.files_info(self.mod_path,self.active_block)
            self.folders()
                    
                    
                


    def changed_folder(self, mod_name_e):
        model = self.mod_name_e.get_model()
        index = self.mod_name_e.get_active()
        name = model[index][0]
        if name=="Select some module":
            self.mod  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

		
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
        no_of_blks=len(self.block_list)
        self.block_list=self.get_blk_list(self.mod_path)
        if not self.block_list:
            self.block_name_e.set_sensitive(False)
            for i in range(0,no_of_blks):
                self.block_name_e.remove_text(no_of_blks-1-i)
            self.lib_e.set_sensitive(False)
            self.include_e.set_sensitive(False)
            #self.swig_e.set_sensitive(False)
            self.grc_e.set_sensitive(False)
            #self.python.set_sensitive(False)
        else:
            self.block_name_e.set_sensitive(True)
            for i in range(0,no_of_blks):
                self.block_name_e.remove_text(no_of_blks-1-i)
            for i in self.block_list:
                self.block_name_e.append_text(i)
            self.block_name_e.set_active(0)
            self.active_block=self.block_name_e.get_active_text()
            self.files_info(self.mod_path,self.active_block)
            self.folders()

    def folders(self):
       
        if self.lib_fold is True:
            self.lib_e.set_sensitive(True)
        else:
            self.lib_e.set_sensitive(False)
        if self.include_fold is True:
            self.include_e.set_sensitive(True)
        else:
            self.include_e.set_sensitive(False)
        if self.grc_fold is True:
            self.grc_e.set_sensitive(True)
        else:
            self.grc_e.set_sensitive(False)




    def run(self):

        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_OK:

            if self.lib_e.entry.get_text()=='Yes':
                self.lib=True
            if self.include_e.entry.get_text()=='Yes':
                self.include=True
            '''if self.swig_e.entry.get_text()=='Yes':
                self.swig=True
            if self.python_e.entry.get_text()=='Yes':
                self.python=True'''
            if self.grc_e.entry.get_text()=='Yes':
                self.grc=True
            try:
                fold_name=self.mod_path.split('/')[-1]
                modname=fold_name.split('-')[1]
                if (fold_name.split('-')[0]=='gr'):
                    rmblock=ModToolRemoveGRC(self.lib, self.include, self.swig, self.grc, self.python,self.mod_path)
                    rmblock.setup(modname, self.block_name_e.get_active_text())
                    rmblock.run()
                else:
                    Errorbox('No GNU Radio module found in the given directory. Quitting.')
            except IndexError:
                Errorbox('No GNU Radio module found in the given directory. Quitting.')
        elif response == gtk.RESPONSE_REJECT:
            pass
        self.destroy()
        return response == gtk.RESPONSE_OK
	

