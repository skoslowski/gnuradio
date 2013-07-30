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
		okbut3 = gtk.Button("Enter")
		path_hbox.pack_end(okbut3,False)
		okbut3.set_size_request(110,-1)
		okbut3.connect("pressed", self.chooser_c,)
		okbut3.show()
		self.path_e = gtk.Entry()
		self.path_e.set_size_request(200,-1)
		path_hbox.pack_end(self.path_e,False)
		self.path_e.show()
		
		bname_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(bname_hbox,False,False,10)
		bname_hbox.show()

		
		bname_l = gtk.Label("Enter block name")
		bname_hbox.pack_start(bname_l,False,False,10)	
		bname_l.show()
		self.bname_e = gtk.Entry()
		self.bname_e.set_size_request(310,-1)
		bname_hbox.pack_end(self.bname_e,False)
		self.bname_e.show()
		
		tname_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(tname_hbox,False,False,10)
		tname_hbox.show()

		
		tname_l = gtk.Label("Enter block type")
		tname_hbox.pack_start(tname_l,False,False,10)	
		tname_l.show()
		self.tname_e = gtk.Combo()
		self.tname_e.set_size_request(310,-1)
		tname_hbox.pack_end(self.tname_e,False)
		self.tname_e.entry.set_text("general")
		slist = [ "general","sink", "source", "sync", "decimator", "interpolator","tagged_stream", "hier", "noblock"]	
		self.tname_e.set_popdown_strings(slist)
		self.tname_e.show()
	
		
		aname_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(aname_hbox,False,False,10)
		aname_hbox.show()

		
		aname_l = gtk.Label("Enter args")
		aname_hbox.pack_start(aname_l,False,False,10)	
		aname_l.show()
		self.aname_e = gtk.Entry()
		self.aname_e.set_size_request(310,-1)
		aname_hbox.pack_end(self.aname_e,False)
		self.aname_e.show()
		


		
		qap_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(qap_hbox,False,False,10)
		qap_hbox.show()

		
		qap_l = gtk.Label("Add Python QA code?")
		qap_hbox.pack_start(qap_l,False,False,10)	
		qap_l.show()
		self.qap_e = gtk.Combo()
		self.qap_e.set_size_request(310,-1)
		qap_hbox.pack_end(self.qap_e,False)
		self.qap_e.entry.set_text("No")
		slist = [ "No","Yes"]	
		self.qap_e.set_popdown_strings(slist)
		self.qap_e.show()

		qac_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(qac_hbox,False,False,10)
		qac_hbox.show()

		qac_l = gtk.Label("Add C++ QA code?")
		qac_hbox.pack_start(qac_l,False,False,10)	
		qac_l.show()
		self.qac_e = gtk.Combo()
		self.qac_e.set_size_request(310,-1)
		qac_hbox.pack_end(self.qac_e,False)
		self.qac_e.entry.set_text("No")
		slist = [ "No","Yes"]	
		self.qac_e.set_popdown_strings(slist)
		self.qac_e.show()

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
			fold_name=self.path_e.get_text().split('/')[len(self.path_e.get_text().split('/'))-1]
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
		self.addblock._info['blocktype'] = self.tname_e.entry.get_text()
		self.addblock._info['lang'] = 'cpp'
		if self.addblock._info['lang'] == 'c++':
		    self.addblock._info['lang'] = 'cpp'
		#print "Language: %s" % {'cpp': 'C++', 'python': 'Python'}[self.addblock._info['lang']]

		if ((self.addblock._skip_subdirs['lib'] and self.addblock._info['lang'] == 'cpp')
		     or (self.addblock._skip_subdirs['python'] and self.addblock._info['lang'] == 'python')):
		    self.Errorbox("Missing or skipping relevant subdir.")
		    return False

		self.addblock._info['blockname']=self.bname_e.get_text()
		
		if not re.match('[a-zA-Z0-9_]+', self.addblock._info['blockname']):
		    self.Errorbox('Invalid block name.')
		    return False
		#print "Block/code identifier: " + self.addblock._info['blockname']
		self.addblock._info['fullblockname'] = self.addblock._info['modname'] + '_' + self.addblock._info['blockname']
		self.addblock._info['license'] = self.addblock.setup_choose_license()
		self.addblock._info['arglist'] = self.aname_e.get_text()
		
		if not (self.addblock._info['blocktype'] in ('noblock') or self.addblock._skip_subdirs['python']):
		    self.addblock._add_py_qa = False
		    if self.qap_e.entry.get_text() is 'No':
		        self.addblock._add_py_qa = False
		    else:
			self.addblock._add_py_qa = True
		if self.addblock._info['lang'] == 'cpp' :
		    if self.qac_e.entry.get_text() is 'No':
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
