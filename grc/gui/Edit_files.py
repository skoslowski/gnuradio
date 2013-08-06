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
import re
from subprocess import Popen, PIPE

	
class edit_files:
    


	def __init__(self):
		
		
		self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
		self.root.set_size_request(600, 200)
		self.root.set_position(gtk.WIN_POS_CENTER)
		self.root.set_border_width(10)
		self.root.set_title("Edit files")
		self.root.connect("destroy",self.destroy)
		self.modname=''
		vbox = gtk.VBox(gtk.FALSE,0)		
		self.root.add(vbox)
		vbox.show()

		editor_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(editor_hbox,False,False,10)
		editor_hbox.show()
		
		editor_l = gtk.Label("Choose your editor for .cc file")
		editor_hbox.pack_start(editor_l,False,False,10)	
		editor_l.show()
		self.editor_e = gtk.combo_box_new_text()
		self.editor_e.set_size_request(310,-1)
		editor_hbox.pack_end(self.editor_e,False)
		print gr.prefs().get_string('my', 'cc_editor', '')+"     yes"
		#self.editor_e.entry.set_text(gr.prefs().get_string('my', 'cc_editor', 'Gedit'))
		#self.slist = [ gr.prefs().get_string('my', 'cc_editor', 'Gedit')]
		self.editor_e.append_text(gr.prefs().get_string('my', 'cc_editor', 'Gedit'))
		lst=['Eclipse','Gedit']	
		for i in lst:
			if re.match(i, gr.prefs().get_string('my', 'cc_editor', 'Gedit')):
				pass
			else:
				self.editor_e.append_text(i)
		#self.editor_e.set_popdown_strings(slist)
		self.editor_e.connect('changed', self.changed_cb)
        	self.editor_e.set_active(0)
		self.editor_e.show()

		file_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(file_hbox,False,False,10)
		file_hbox.show()

		file_l = gtk.Label("Choose file")
		file_hbox.pack_start(file_l,False,False,10)	
		file_l.show()
		okbut3 = gtk.Button("Enter")
		file_hbox.pack_end(okbut3,False)
		okbut3.set_size_request(110,-1)
		okbut3.connect("pressed", self.chooser_c,)
		okbut3.show()
		self.file_e = gtk.Entry()
		self.file_e.set_size_request(200,-1)
		file_hbox.pack_end(self.file_e,False)
		self.file_e.show()

	

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


	def changed_cb(self, editor_e):
		ins = open(os.path.expanduser('~/.gnuradio/config.conf'), "r" )
		array = []
		check=False
		for line in ins:
			print line+'1'
		        if 'cc_editor=' in line.lower():
		            print line+'2'
		        else:
		            print line+'3'
		            array.append( line )
		print editor_e.get_model()[editor_e.get_active()][0]
		array.append('cc_editor='+editor_e.get_model()[editor_e.get_active()][0])
		f = open(os.path.expanduser('~/.gnuradio/config.conf'),'w')
		for line in array:
			f.write(line)
		return

	def chooser_c(self,w):	
		self.fold_cr  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

		
		self.fold_cr.show()
		response = self.fold_cr.run()
		if response == gtk.RESPONSE_OK:
		    self.new_f_name=self.fold_cr.get_filename()
		    self.file_e.set_text(self.new_f_name)
		    self.fold_cr.destroy()

		if response == gtk.RESPONSE_CANCEL:
		    self.fold_cr.destroy()

	
	def destroy(self,widget):
		gtk.mainquit()
		

	
	def collect_entry(self, pwidget):			
		try:
			if os.path.exists(self.file_e.get_text()):
				if re.match("Eclipse", self.editor_e.get_model()[self.editor_e.get_active()][0]):
					Popen(['eclipse',self.file_e.get_text()],stdout=PIPE)
				if re.match("Gedit", self.editor_e.get_model()[self.editor_e.get_active()][0]):
					Popen(['gedit',self.file_e.get_text()],stdout=PIPE)
				print gr.prefs().get_string('my', 'cc_editor', '')+'no'
			else:
				self.Errorbox('File not found')
		except IOError:
			self.Errorbox('File not found')
	
	def mainloop(self):
		gtk.mainloop()


	def Errorbox(self,err_msg): 
		message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
		message.set_markup(err_msg)
		message.run()
		message.destroy()
