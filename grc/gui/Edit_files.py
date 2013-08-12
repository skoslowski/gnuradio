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
""" Module to edit files in project folder """
import gtk
import sys
import os
from os.path import expanduser
from gnuradio import gr
import re
from subprocess import Popen, PIPE
import ConfigParser

	
class edit_files:
    
    def __init__(self):

        self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
        self.root.set_size_request(600, 200)
        self.root.set_position(gtk.WIN_POS_CENTER)
        self.root.set_border_width(10)
        self.root.set_title("Edit files")
        self.root.connect("destroy",self.destroy)
        vbox = gtk.VBox(gtk.FALSE,0)		
        self.root.add(vbox)
        vbox.show()


        edit_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(edit_hbox,False,False,10)
        edit_hbox.show()

        edit_l = gtk.Label("Select your editor's path")
        edit_hbox.pack_start(edit_l,False,False,10)	
        edit_l.show()
        enter_but = gtk.Button("Enter")
        edit_hbox.pack_end(enter_but,False)
        enter_but.set_size_request(110,-1)
        enter_but.connect("pressed", self.chooser_c,)
        enter_but.show()
        self.edit_e = gtk.Entry()
        self.edit_e.set_size_request(200,-1)
        edit_hbox.pack_end(self.edit_e,False)
        self.edit_e.show()

	

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

    def executable_filter(self, filter_info, data):
        path = filter_info[0]
        return os.access(path, os.X_OK)


    def chooser_c(self,w):	
        self.file_path_name  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

        filter_file = gtk.FileFilter()
        filter_file.set_name("executable files")
        filter_file.add_custom(gtk.FILE_FILTER_FILENAME, self.executable_filter, None)
        self.file_path_name.add_filter(filter_file)
        self.file_path_name.show()
        response = self.file_path_name.run()
        if response == gtk.RESPONSE_OK:
            self.new_f_name=self.file_path_name.get_filename()
            self.edit_e.set_text(self.new_f_name)
            self.file_path_name.destroy()

        if response == gtk.RESPONSE_CANCEL:
            self.file_path_name.destroy()

	
    def destroy(self,widget):
        gtk.mainquit()
		

    def collect_entry(self, pwidget):
        global editor
        conf_path='%s/.gnuradio/config.conf' % os.path.expanduser("~")			
        if os.path.exists(self.edit_e.get_text()):
            editor=self.edit_e.get_text()
            config = ConfigParser.ConfigParser()
            config.read(conf_path)
            if config.has_section('editors'):
                config.remove_section('editors')
                with open(conf_path, 'w') as configfile:
                    config.write(configfile)
                configadd = ConfigParser.ConfigParser()
                configadd.add_section('editors')
                configadd.set('editors', 'editor', editor)
                with open(conf_path, 'a') as configfile:
                    configadd.write(configfile)
            else:
                configadd = ConfigParser.ConfigParser()
                configadd.add_section('editors')
                configadd.set('editors', 'editor', editor)
                with open(conf_path, 'a') as configfile:
                    configadd.write(configfile)
            os.chdir(editor.rsplit(editor.split('/')[-1], 1)[0])
            Popen([editor.split('/')[-1]],stdout=PIPE)
        else:
            self.Errorbox('File not found')

	
    def mainloop(self):
        gtk.mainloop()


    def Errorbox(self,err_msg): 
        message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        message.set_markup(err_msg)
        message.run()
        message.destroy()

def editor_path():
    global editor
    try:
        if editor:
            return editor
    except NameError:
        return None


