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
from subprocess import Popen, PIPE
from Messages import open_doc_and_code_message
import pexpect
	
class install_block:
    


    def __init__(self):

        self.root = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
        self.root.set_size_request(600, 220)
        self.root.set_position(gtk.WIN_POS_CENTER)
        self.root.set_border_width(10)
        self.root.set_title("Install block")
        self.root.connect("destroy",self.destroy)
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
		
        password_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(password_hbox,False,False,10)
        password_hbox.show()

		
        password_l = gtk.Label("Enter password [sudo]")
        password_hbox.pack_start(password_l,False,False,10)	
        password_l.show()
        self.password_e = gtk.Entry()
        self.password_e.set_size_request(310,-1)
        password_hbox.pack_end(self.password_e,False)
        self.password_e.set_visibility(False)
        self.password_e.show()

        end_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_end(end_hbox,False,False,10)
        end_hbox.show()

        self.okbut = gtk.Button("Install")
        end_hbox.pack_end(self.okbut,False)
        self.okbut.set_size_request(100,-1)
        self.okbut.connect("pressed", self.collect_entry,)
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

	
	

    def collect_entry(self, pwidget):

        if os.path.isdir(self.path_e.get_text()):
            os.chdir(self.path_e.get_text())
            if True:
                os.chdir(self.path_e.get_text()+'/build')
                cmake_op=Popen(['cmake','-DENABLE_DOXYGEN=ON', '../'],stdout=PIPE)
                open_doc_and_code_message(cmake_op.stdout.read())
                open_doc_and_code_message('\n---------------------------------------------------\n')
                #install_op=os.system('echo %s|sudo -S make install' %self.password_e.get_text())-DENABLE_DOXYGEN=ON 
                child = pexpect.spawn('sudo make install')
                child.expect(['ssword', pexpect.EOF])
                child.sendline(self.password_e.get_text())
                child.expect(pexpect.EOF)
                open_doc_and_code_message(child.before)
                open_doc_and_code_message('\n\n')
                child.close()

            else:
                self.Errorbox('Installation Error.')
        else:
            self.Errorbox('No GNU Radio module found in the given directory. Quitting.')
		
    def mainloop(self):
        gtk.mainloop()

	

    def Errorbox(self,err_msg): 
        message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        message.set_markup(err_msg)
        message.run()
        message.destroy()
