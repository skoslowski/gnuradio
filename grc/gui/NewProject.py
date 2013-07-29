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
from gnuradio import gr
from os.path import expanduser
sys.path.append(gr.prefs().get_string('grc', 'source_path', '')+'/gr-utils/python/modtool')
from modtool_newmod import ModToolNewModule
import re
from modtool_base import ModTool
from Dialogs import MessageDialogHelper
from MainWindow import MainWindow
from .. base import ParseXML

class add_module:
    


	def __init__(self,win):
		
		
		self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
	        self.root.set_size_request(550, 170)
		self.root.set_position(gtk.WIN_POS_CENTER)
	        self.root.set_border_width(10)
	        self.root.set_title("Create new project folder")
		self.root.connect("destroy",self.destroy)
		self.f_name=""
		self.new_f_name=""
		self.main_window = win
		vbox = gtk.VBox(gtk.FALSE,0)		
		self.root.add(vbox)
		vbox.show()
		
		fname_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(fname_hbox,False,False,10)
		fname_hbox.show()

		
		fname_l = gtk.Label("Enter folder/module name")
		fname_hbox.pack_start(fname_l,False,False,10)	
		fname_l.show()
		self.fname_e = gtk.Entry()
		self.fname_e.set_size_request(310,-1)
		fname_hbox.pack_end(self.fname_e,False)
		self.fname_e.show()


		path_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(path_hbox,False,False,10)
		path_hbox.show()

		path_l = gtk.Label("Choose folder location")
		path_hbox.pack_start(path_l,False,False,10)	
		path_l.show()
		okbut3 = gtk.Button("Enter")
		path_hbox.pack_end(okbut3,False)
		okbut3.set_size_request(110,-1)
		okbut3.connect("pressed", self.chooser_c,)
		okbut3.show()
		self.path_e = gtk.Entry()
		self.path_e.set_size_request(200,-1)
		path_hbox.pack_end(self.path_e,False)
		self.path_e.show()

				


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

		os.chdir(self.path_e.get_text())
		self.newmod=ModToolNewModule()	
		ModToolNewModule.setup=self.setupnewmod
		if self.newmod.setup() is True:
			self.newmod.run()
		file_path=self.path_e.get_text()+"/gr-"+self.fname_e.get_text()+"/apps/main.grc"
		self.main_window.new_page()
		self.main_window.get_page().set_file_path(file_path)
		ParseXML.to_file(self.main_window.get_flow_graph().export_data(), self.main_window.get_page().get_file_path());
		self.main_window.get_flow_graph().grc_file_path = "/"+self.main_window.get_page().get_file_path()
		self.main_window.get_page().set_saved(True)		
				
	
	def mainloop(self):
		gtk.mainloop()


	def setupnewmod(self):

		self.newmod._info['modname'] = self.fname_e.get_text()
		if not re.match('[a-zA-Z0-9_]+', self.newmod._info['modname']):
		    self.Errorbox('Invalid module name.')
		    return False
		self.newmod._dir = './gr-%s' % self.newmod._info['modname']
		try:
		    os.stat(self.newmod._dir)
		except OSError:
		    pass # This is what should happen
		else:
		    self.Errorbox('The given directory exists.')
		    return False
		self.newmod._srcdir = gr.prefs().get_string('modtool', 'newmod_path', '/usr/local/share/gnuradio/modtool/gr-newmod')
		if not os.path.isdir(self.newmod._srcdir):
		    self.Errorbox('Could not find gr-newmod source dir.')
		    return False
		return True

	def Errorbox(self,err_msg): 
		message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
		message.set_markup(err_msg)
		message.run()
		message.destroy()
	

