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
sys.path.append(gr.prefs().get_string('grc', 'source_path', '')+'/gr-utils/python/modtool')
from modtool_add import ModToolAdd
import re
from modtool_base import ModTool
from Dialogs import MessageDialogHelper
from MainWindow import MainWindow
from .. base import ParseXML


	
class add_new_block:
    


    def __init__(self):
		
		
        self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
        self.root.set_size_request(600, 400)
        self.root.set_position(gtk.WIN_POS_CENTER)
        self.root.set_border_width(10)
        self.root.set_title("Add new block")
        self.root.connect("destroy",self.destroy)
        self.modname=''
        vbox = gtk.VBox(gtk.FALSE,0)		
        self.root.add(vbox)
        vbox.show()

        path_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(path_hbox,False,False,10)
        path_hbox.show()

        path_l = gtk.Label("Choose block location (e.g. gr-howto)")
        path_hbox.pack_start(path_l,False,False,10)	
        path_l.show()
        enter_but = gtk.Button("Enter")
        path_hbox.pack_end(enter_but,False)
        enter_but.set_size_request(110,-1)
        enter_but.connect("pressed", self.chooser_c,)
        enter_but.show()
        self.path_e = gtk.Entry()
        self.path_e.set_size_request(200,-1)
        path_hbox.pack_end(self.path_e,False)
        self.path_e.show()
		
        block_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(block_name_hbox,False,False,10)
        block_name_hbox.show()

		
        block_name_l = gtk.Label("Enter block name")
        block_name_hbox.pack_start(block_name_l,False,False,10)	
        block_name_l.show()
        self.block_name_e = gtk.Entry()
        self.block_name_e.set_size_request(310,-1)
        block_name_hbox.pack_end(self.block_name_e,False)
        self.block_name_e.show()
		
        type_name_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(type_name_hbox,False,False,10)
        type_name_hbox.show()

		
        type_name_l = gtk.Label("Enter block type")
        type_name_hbox.pack_start(type_name_l,False,False,10)	
        type_name_l.show()
        self.type_name_e = gtk.Combo()
        self.type_name_e.set_size_request(310,-1)
        type_name_hbox.pack_end(self.type_name_e,False)
        self.type_name_e.entry.set_text("general")
        slist = [ "general","sink", "source", "sync", "decimator", "interpolator","tagged_stream", "hier", "noblock"]	
        self.type_name_e.set_popdown_strings(slist)
        self.type_name_e.show()
	
		
        arg_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(arg_hbox,False,False,10)
        arg_hbox.show()

		
        arg_l = gtk.Label("Enter args")
        arg_hbox.pack_start(arg_l,False,False,10)	
        arg_l.show()
        self.arg_e = gtk.Entry()
        self.arg_e.set_size_request(310,-1)
        arg_hbox.pack_end(self.arg_e,False)
        self.arg_e.show()
		


		
        qa_python_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(qa_python_hbox,False,False,10)
        qa_python_hbox.show()

		
        qa_python_l = gtk.Label("Add Python QA code?")
        qa_python_hbox.pack_start(qa_python_l,False,False,10)	
        qa_python_l.show()
        self.qa_python_e = gtk.Combo()
        self.qa_python_e.set_size_request(310,-1)
        qa_python_hbox.pack_end(self.qa_python_e,False)
        self.qa_python_e.entry.set_text("No")
        slist = [ "No","Yes"]	
        self.qa_python_e.set_popdown_strings(slist)
        self.qa_python_e.show()

        qa_cpp_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(qa_cpp_hbox,False,False,10)
        qa_cpp_hbox.show()

        qa_cpp_l = gtk.Label("Add C++ QA code?")
        qa_cpp_hbox.pack_start(qa_cpp_l,False,False,10)	
        qa_cpp_l.show()
        self.qa_cpp_e = gtk.Combo()
        self.qa_cpp_e.set_size_request(310,-1)
        qa_cpp_hbox.pack_end(self.qa_cpp_e,False)
        self.qa_cpp_e.entry.set_text("No")
        slist = [ "No","Yes"]	
        self.qa_cpp_e.set_popdown_strings(slist)
        self.qa_cpp_e.show()

        end_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_end(end_hbox,False,False,10)
        end_hbox.show()

        okbut = gtk.Button("OK")
        end_hbox.pack_end(okbut,False)
        okbut.set_size_request(100,-1)
        okbut.connect("pressed", self.collect_entry,)
        okbut.show()
        cancelbut = gtk.Button("Cancel")
        cancelbut.connect_object("clicked", gtk.Widget.destroy, self.root)
        end_hbox.pack_end(cancelbut,False)
        cancelbut.set_size_request(100,-1)
        cancelbut.show()
	
        self.root.show()
        self.mainloop()


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

	
    def destroy(self,widget):
        gtk.mainquit()
		

	
    def collect_entry(self, pwidget):			
        try:
            fold_name=self.path_e.get_text().split('/')[-1]
            self.modname=fold_name.split('-')[1]
            if re.search(fold_name.split('-')[0],'gr'):
                os.chdir(self.path_e.get_text())
                self.addblock=ModToolAdd()
                ModToolAdd.setup=self.setupadd
                if self.addblock.setup() is True:
                    self.addblock.run()
            else:
                self.Errorbox('No GNU Radio module found in the given directory. Quitting.')
        except IndexError:
            self.Errorbox('No GNU Radio module found in the given directory. Quitting')
	
    def mainloop(self):
        gtk.mainloop()

    def setupadd(self):
        ModTool.setup(self.addblock)
        self.addblock._info['modname']=self.modname
        self.addblock._info['blocktype'] = self.type_name_e.entry.get_text()
        self.addblock._info['lang'] = 'cpp'
        if self.addblock._info['lang'] == 'c++':
            self.addblock._info['lang'] = 'cpp'
		#print "Language: %s" % {'cpp': 'C++', 'python': 'Python'}[self.addblock._info['lang']]

        if ((self.addblock._skip_subdirs['lib'] and self.addblock._info['lang'] == 'cpp')
		     or (self.addblock._skip_subdirs['python'] and self.addblock._info['lang'] == 'python')):
            self.Errorbox("Missing or skipping relevant subdir.")
            return False

        self.addblock._info['blockname']=self.block_name_e.get_text()
		
        if not re.match('[a-zA-Z0-9_]+', self.addblock._info['blockname']):
            self.Errorbox('Invalid block name.')
            return False
		#print "Block/code identifier: " + self.addblock._info['blockname']
        self.addblock._info['fullblockname'] = self.addblock._info['modname'] + '_' + self.addblock._info['blockname']
        self.addblock._info['license'] = self.addblock.setup_choose_license()
        self.addblock._info['arglist'] = self.arg_e.get_text()
		
        if not (self.addblock._info['blocktype'] in ('noblock') or self.addblock._skip_subdirs['python']):
            self.addblock._add_py_qa = False
            if self.qa_python_e.entry.get_text() is 'No':
                self.addblock._add_py_qa = False
            else:
        	self.addblock._add_py_qa = True
        if self.addblock._info['lang'] == 'cpp' :
            if self.qa_cpp_e.entry.get_text() is 'No':
                self.addblock._add_cc_qa = False
            else:
                self.addblock._add_cc_qa = True 
		 
        if self.addblock._info['version'] == 'autofoo':
            self.Errorbox("Warning: Autotools modules are not supported.Files will be created, but Makefiles will not be edited.")
        return True

    def Errorbox(self,err_msg): 
        message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        message.set_markup(err_msg)
        message.run()
        message.destroy()
