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
from modtool_base import ModTool
from Dialogs import MessageDialogHelper
from MainWindow import MainWindow
from .. base import ParseXML
import glob
from optparse import OptionGroup
from cmakefile_editor import CMakeFileEditor
from util_functions import remove_pattern_from_file
from modtool_rm import ModToolRemove

	
class remove_block:
    


	def __init__(self):
		
		
		self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
	        self.root.set_size_request(600, 400)
		self.root.set_position(gtk.WIN_POS_CENTER)
	        self.root.set_border_width(10)
	        self.root.set_title("Remove block")
		self.root.connect("destroy",self.destroy)
		self.modname=''
		self.lib=False
		self.include=False
		self.swig=False
		self.python=False
		self.grc=False
		self.okbut = gtk.Button("OK")
		self.python_e = gtk.Combo()
		self.lib_e = gtk.Combo()
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
		
		


		
		lib_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(lib_hbox,False,False,10)
		lib_hbox.show()

		
		lib_l = gtk.Label("Delete files from lib/?")
		lib_hbox.pack_start(lib_l,False,False,10)	
		lib_l.show()
		self.lib_e = gtk.Combo()
		self.lib_e.set_size_request(310,-1)
		lib_hbox.pack_end(self.lib_e,False)
		self.lib_e.entry.set_text("No")
		slist = [ "No","Yes"]	
		self.lib_e.set_popdown_strings(slist)
		self.lib_e.show()

		include_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(include_hbox,False,False,10)
		include_hbox.show()

		
		include_l = gtk.Label("Delete files from include/?")
		include_hbox.pack_start(include_l,False,False,10)	
		include_l.show()
		self.include_e = gtk.Combo()
		self.include_e.set_size_request(310,-1)
		include_hbox.pack_end(self.include_e,False)
		self.include_e.entry.set_text("No")
		slist = [ "No","Yes"]	
		self.include_e.set_popdown_strings(slist)
		self.include_e.show()


		swig_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(swig_hbox,False,False,10)
		swig_hbox.show()

		
		swig_l = gtk.Label("Delete files from swig/?")
		swig_hbox.pack_start(swig_l,False,False,10)	
		swig_l.show()
		self.swig_e = gtk.Combo()
		self.swig_e.set_size_request(310,-1)
		swig_hbox.pack_end(self.swig_e,False)
		self.swig_e.entry.set_text("No")
		slist = [ "No","Yes"]	
		self.swig_e.set_popdown_strings(slist)
		self.swig_e.show()


		grc_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(grc_hbox,False,False,10)
		grc_hbox.show()

		
		grc_l = gtk.Label("Delete files from grc/?")
		grc_hbox.pack_start(grc_l,False,False,10)	
		grc_l.show()
		self.grc_e = gtk.Combo()
		self.grc_e.set_size_request(310,-1)
		grc_hbox.pack_end(self.grc_e,False)
		self.grc_e.entry.set_text("No")
		slist = [ "No","Yes"]	
		self.grc_e.set_popdown_strings(slist)
		self.grc_e.show()

		python_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_start(python_hbox,False,False,10)
		python_hbox.show()

		python_l = gtk.Label("Delete files from python/?")
		python_hbox.pack_start(python_l,False,False,10)	
		python_l.show()
		self.python_e = gtk.Combo()
		self.python_e.set_size_request(310,-1)
		python_hbox.pack_end(self.python_e,False)
		self.python_e.entry.set_text("No")
		slist = [ "No","Yes"]	
		self.python_e.set_popdown_strings(slist)
		self.python_e.show()

		end_hbox = gtk.HBox(gtk.FALSE,0)
		vbox.pack_end(end_hbox,False,False,10)
		end_hbox.show()

		
		end_hbox.pack_end(self.okbut,False)
		self.okbut.set_size_request(100,-1)
		self.okbut.connect("pressed", self.collect_entry_rm,)
		self.okbut.show()
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
		

	
	

	def collect_entry_rm(self, pwidget):		
		if re.search(self.lib_e.entry.get_text(),'Yes'):
			self.lib=True
		if re.search(self.include_e.entry.get_text(),'Yes'):
			self.include=True
		if re.search(self.swig_e.entry.get_text(),'Yes'):
			self.swig=True
		if re.search(self.python_e.entry.get_text(),'Yes'):
			self.python=True
		if re.search(self.grc_e.entry.get_text(),'Yes'):
			self.grc=True
		try:
			fold_name=self.path_e.get_text().split('/')[len(self.path_e.get_text().split('/'))-1]
			self.modname=fold_name.split('-')[1]
			if re.search(fold_name.split('-')[0],'gr'):
				os.chdir(self.path_e.get_text())
				print self.path_e.get_text()
				self.rmblock=ModToolRemove()
				ModToolRemove.setup=self.setuprm
				ModToolRemove._run_subdir=self._run_subdir_rm
				self.rmblock.setup()
				self.rmblock.run()
			else:
				self.Errorbox('No GNU Radio module found in the given directory. Quitting.')
		except IndexError:
			self.Errorbox('No GNU Radio module found in the given directory. Quitting.')
	
	def mainloop(self):
		gtk.mainloop()

	
 
	def setuprm(self):
		self.rmblock._info['modname']=self.modname
		ModTool.setup(self.rmblock)
		print "yes"
		self.rmblock._info['pattern'] = self.bname_e.get_text()
		if len(self.rmblock._info['pattern']) == 0:
		    self.rmblock._info['pattern'] = '.'
	def _run_subdir_rm(self, path, globs, makefile_vars, cmakeedit_func=None):
        
        # 1. Create a filtered list
		files = []
		for g in globs:
		    files = files + glob.glob("%s/%s"% (path, g))
		files_filt = []
		print "Searching for matching files in %s/:" % path
		for f in files:
		    if re.search(self.rmblock._info['pattern'], os.path.basename(f)) is not None:
		        files_filt.append(f)
		if len(files_filt) == 0:
		    print "None found."
		    return []
		# 2. Delete files, Makefile entries and other occurences
		files_deleted = []
		ed = CMakeFileEditor('%s/CMakeLists.txt' % path)
		for f in files_filt:
		    b = os.path.basename(f)
		    if 'lib' in f.lower():
		    	yes = self.lib
		    if 'include' in f.lower():
		    	yes = self.include
		    if 'swig' in f.lower():
		    	yes = self.swig
		    if 'python' in f.lower():
		    	yes = self.python
		    if 'grc' in f.lower():
		    	yes = self.grc
		    if yes is False:
			continue

		    files_deleted.append(b)
		    print "Deleting %s." % f
		    os.unlink(f)
		    print "Deleting occurrences of %s from %s/CMakeLists.txt..." % (b, path)
		    for var in makefile_vars:
		        ed.remove_value(var, b)
		    if cmakeedit_func is not None:
		        cmakeedit_func(b, ed)
		ed.write()
		return files_deleted
          

	def Errorbox(self,err_msg): 
		message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
		message.set_markup(err_msg)
		message.run()
		message.destroy()
