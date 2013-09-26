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
from Messages import OTM_message
from Preferences import get_OOT_module, add_OOT_module, get_editor
from EditFilesDialog import EditFilesDialog, editor_path
from subprocess import Popen, PIPE

	
class AddBlockDialog(gtk.Dialog): 

    """
    A dialog to add blocks in out of tree module.
    """

    def __init__(self):
        """
        dialog contructor.
        """
        gtk.Dialog.__init__(self,
            title="Add new block",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )



        self.set_size_request(600, 220)
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

	#create an entry box to enter block name.
        self.block_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.block_hbox,False,False,7)
        self.block_hbox.show()

		
        self.block_label = gtk.Label("Enter block name")
        self.block_hbox.pack_start(self.block_label,False)	
        self.block_label.show()
        self.block_entry = gtk.Entry()
        self.block_label.set_size_request(250,-1)
        self.block_hbox.pack_start(self.block_entry,True)
        self.block_entry.show()

	#create an entry box to enter block type.
        self.type_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.type_hbox,False,False,7)
        self.type_hbox.show()

		
        self.type_label = gtk.Label("Enter block type")
        self.type_hbox.pack_start(self.type_label,False)	
        self.type_label.show()
        self.type_entry = gtk.Combo()
        self.type_label.set_size_request(250,-1)
        self.type_hbox.pack_start(self.type_entry,True)
        self.type_entry.entry.set_text("general")
        slist = [ "general","sink", "source", "sync", "decimator", "interpolator","tagged_stream", "hier", "noblock"]	
        self.type_entry.set_popdown_strings(slist)
        self.type_entry.show()

	#create an entry box to enter arguments.
        self.arg_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.arg_hbox,False,False,7)
        self.arg_hbox.show()

		
        self.arg_label = gtk.Label("Enter args")
        self.arg_hbox.pack_start(self.arg_label,False)	
        self.arg_label.show()
        self.arg_entry = gtk.Entry()
        self.arg_label.set_size_request(250,-1)
        self.arg_hbox.pack_start(self.arg_entry,True)
        self.arg_entry.show()
	
        self.show_all()

    def handle_change(self, module_entry):

        """
        any change in module selection will update the /.grc config file.
        file chooser dialog can also be opened to choose some other module.
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

    def open_files(self,editor,h_file,cc_file,xml_file,py_file):

        """
        Open the files in user's selected editor.
        """
        if os.path.exists(h_file): 
            OTM_message('Opening file "%s.h" from "%s".\n' %(self.block_entry.get_text(), self.mod_path))
            Popen([editor,h_file],stdout=PIPE)
        if os.path.exists(cc_file):
            OTM_message('Opening file "%s_impl.cc" from "%s".\n' %(self.block_entry.get_text(), self.mod_path))
            Popen([editor,cc_file],stdout=PIPE)
        if os.path.exists(xml_file):
            OTM_message('Opening file "%s_%s.xml" from "%s".\n' %(self.mod_path.split('/')[-1].split('-')[1], self.block_entry.get_text(), self.mod_path))
            Popen([editor,xml_file],stdout=PIPE)
        if os.path.exists(py_file):
            OTM_message('Opening file "%s.py" from "%s".\n' %(self.block_entry.get_text(), self.mod_path))
            Popen([editor,py_file],stdout=PIPE)



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
                    module_name=self.mod_path.split('/')[-1]
                    modname=module_name.split('-')[1]
                    if module_name.split('-')[0]=='gr':
                        if os.path.isdir(self.mod_path):
                            #borrowed version of ModToolAdd for GRC.
                            addblock=ModToolAddGRC(self.mod_path,modname, self.type_entry.entry.get_text(), self.block_entry.get_text(), self.arg_entry.get_text())
                            try:
                                addblock.setup()
                                addblock.run()
                                OTM_message('Block "%s" has been added in "%s".\n' % (self.block_entry.get_text(), self.mod_path))
                                #get the user's selected editor path
                                editor=get_editor()
                                #set the locations of all source files.
                                h_path='%s/include/%s/%s.h'%(self.mod_path,modname,self.block_entry.get_text())
                                cc_path='%s/lib/%s_impl.cc'%(self.mod_path,self.block_entry.get_text())
                                xml_path='%s/grc/%s_%s.xml'%(self.mod_path,modname,self.block_entry.get_text())
                                py_path='%s/python/%s.py'%(self.mod_path,self.block_entry.get_text())
                                #select editor if it has not been selected.
                                if editor is None:
                                    EditFilesDialog().run()
                                    editor=get_editor()
                                    self.open_files(editor,h_path, cc_path, xml_path, py_path)
                                else:
                                    self.open_files(editor,h_path, cc_path, xml_path, py_path)
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

	

