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
from ModtoolGRC import ModToolAddGRC, Errorbox, ModToolException
import re
from Messages import project_folder_message
from Preferences import get_OOT_module, add_OOT_module, get_editor
from EditFilesDialog import EditFilesDialog, editor_path
from subprocess import Popen, PIPE

	
class AddBlockDialog(gtk.Dialog):
    


    def __init__(self):

        gtk.Dialog.__init__(self,
            title="Add new block",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )



        self.set_size_request(600, 220)
        vbox = gtk.VBox()
        self.vbox.pack_start(vbox, True, True, 0)
       

        self.mod_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.mod_hbox,False,False,7)
        self.mod_hbox.show()

        self.mod_path=''
        self.mod_name_l = gtk.Label("Choose block location")
        self.mod_hbox.pack_start(self.mod_name_l,False)	
        self.mod_name_l.show()
        self.mod_name_e = gtk.combo_box_new_text()
        self.mod_name_l.set_size_request(250,-1)
        self.mod_hbox.pack_start(self.mod_name_e,True)
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
        self.mod_name_e.connect('changed', self.handle_change)
        self.mod_name_e.show()

        self.block_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.block_name_hbox,False,False,7)
        self.block_name_hbox.show()

		
        self.block_name_l = gtk.Label("Enter block name")
        self.block_name_hbox.pack_start(self.block_name_l,False)	
        self.block_name_l.show()
        self.block_name_e = gtk.Entry()
        self.block_name_l.set_size_request(250,-1)
        self.block_name_hbox.pack_start(self.block_name_e,True)
        self.block_name_e.show()

        self.type_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.type_name_hbox,False,False,7)
        self.type_name_hbox.show()

		
        self.type_name_l = gtk.Label("Enter block type")
        self.type_name_hbox.pack_start(self.type_name_l,False)	
        self.type_name_l.show()
        self.type_name_e = gtk.Combo()
        self.type_name_l.set_size_request(250,-1)
        self.type_name_hbox.pack_start(self.type_name_e,True)
        self.type_name_e.entry.set_text("general")
        slist = [ "general","sink", "source", "sync", "decimator", "interpolator","tagged_stream", "hier", "noblock"]	
        self.type_name_e.set_popdown_strings(slist)
        self.type_name_e.show()

        self.arg_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.arg_name_hbox,False,False,7)
        self.arg_name_hbox.show()

		
        self.arg_name_l = gtk.Label("Enter args")
        self.arg_name_hbox.pack_start(self.arg_name_l,False)	
        self.arg_name_l.show()
        self.arg_name_e = gtk.Entry()
        self.arg_name_l.set_size_request(250,-1)
        self.arg_name_hbox.pack_start(self.arg_name_e,True)
        self.arg_name_e.show()
	
        self.show_all()

    def handle_change(self, mod_name_e):
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

    def open_files(self,edtr,h_file,cc_file,xml_file,py_file):
        if os.path.exists(h_file): 
            project_folder_message('Opening file "%s.h" from "%s".\n' %(self.block_name_e.get_text(), self.mod_path))
            Popen([edtr,h_file],stdout=PIPE)
        if os.path.exists(cc_file):
            project_folder_message('Opening file "%s_impl.cc" from "%s".\n' %(self.block_name_e.get_text(), self.mod_path))
            Popen([edtr,cc_file],stdout=PIPE)
        if os.path.exists(xml_file):
            project_folder_message('Opening file "%s_%s.xml" from "%s".\n' %(self.mod_path.split('/')[-1].split('-')[1], self.block_name_e.get_text(), self.mod_path))
            Popen([edtr,xml_file],stdout=PIPE)
        if os.path.exists(py_file):
            project_folder_message('Opening file "%s.py" from "%s".\n' %(self.block_name_e.get_text(), self.mod_path))
            Popen([edtr,py_file],stdout=PIPE)



    def run(self):
        run_again=True
        while run_again:
            response = gtk.Dialog.run(self)
            if response == gtk.RESPONSE_OK:
                try:
                    fold_name=self.mod_path.split('/')[-1]
                    modname=fold_name.split('-')[1]
                    if fold_name.split('-')[0]=='gr':
                        if os.path.isdir(self.mod_path):
                            addblock=ModToolAddGRC(self.mod_path,modname, self.type_name_e.entry.get_text(), self.block_name_e.get_text(), self.arg_name_e.get_text())
                            try:
                                addblock.setup()
                                addblock.run()
                                project_folder_message('Block "%s" has been added in "%s".\n' % (self.block_name_e.get_text(), self.mod_path))
                                edtr=get_editor()
                                h_path='%s/include/%s/%s.h'%(self.mod_path,modname,self.block_name_e.get_text())
                                cc_path='%s/lib/%s_impl.cc'%(self.mod_path,self.block_name_e.get_text())
                                xml_path='%s/grc/%s_%s.xml'%(self.mod_path,modname,self.block_name_e.get_text())
                                py_path='%s/python/%s.py'%(self.mod_path,self.block_name_e.get_text())
                                if edtr is None:
                                    EditFilesDialog().run()
                                    edtr=get_editor()
                                    self.open_files(edtr,h_path, cc_path, xml_path, py_path)
                                else:
                                    self.open_files(edtr,h_path, cc_path, xml_path, py_path)
                                run_again=False
                            except ModToolException:
                                pass                               
                        else:
                            Errorbox('%s is not found'% self.mod_path)
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

	

