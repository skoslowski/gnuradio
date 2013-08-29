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
import pexpect
from ModtoolGRC import Errorbox
from Messages import project_folder_message


	
class InstallBlockDialog(gtk.Dialog):
    


    def __init__(self):


        gtk.Dialog.__init__(self,
            title="Create new module",
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_OK),
        )

        self.set_size_request(600, 170)
        vbox = gtk.VBox()
        self.vbox.pack_start(vbox, True, True, 0)

        self.path_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.path_hbox,False,False,7)
        self.path_hbox.show()

        self.path_l = gtk.Label("Choose block location")
        self.path_hbox.pack_start(self.path_l,False)	
        self.path_l.show()
        self.enter_but = gtk.Button("...")
        self.path_hbox.pack_end(self.enter_but,False)
        self.enter_but.set_size_request(70,-1)
        self.enter_but.connect("pressed", self.choose_folder,)
        self.enter_but.show()
        self.path_e = gtk.Entry()
        self.path_l.set_size_request(250,-1)
        self.path_hbox.pack_start(self.path_e,True)
        self.path_e.show()


        self.password_hbox = gtk.HBox(gtk.FALSE,0)
        vbox.pack_start(self.password_hbox,False,False,7)
        self.password_hbox.show()

		
        self.password_l = gtk.Label("Enter password [sudo]")
        self.password_hbox.pack_start(self.password_l,False)	
        self.password_l.show()
        self.password_e = gtk.Entry()
        self.password_l.set_size_request(250,-1)
        self.password_e.set_visibility(False)
        self.password_hbox.pack_start(self.password_e,True)
        self.password_e.show()

        self.show_all()


		
    def choose_folder(self,w):	
        self.fold_path_name  = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

        self.fold_path_name.set_current_folder(os.path.expanduser('~'))
        self.fold_path_name.show()
        response = self.fold_path_name.run()
        if response == gtk.RESPONSE_OK:
            self.path_e.set_text(self.fold_path_name.get_filename())
            self.fold_path_name.destroy()
        if response == gtk.RESPONSE_CANCEL:
            self.fold_path_name.destroy()

    def run(self):

        run_again=True
        while run_again:
            response = gtk.Dialog.run(self)
            if response == gtk.RESPONSE_OK:

                if os.path.isdir(self.path_e.get_text()) and '/gr-' in self.path_e.get_text().lower():
                    path=os.getcwd()
                    os.chdir(self.path_e.get_text()+'/build')
                    cmake_op=Popen(['cmake','-DENABLE_DOXYGEN=ON','../'],stdout=PIPE)
                    project_folder_message(cmake_op.stdout.read())
                    project_folder_message('\n---------------------------------------------------\n')
                    #install_op=os.system('echo %s|sudo -S make install' %self.password_e.get_text())-DENABLE_DOXYGEN=ON 
                    child = pexpect.spawn('sudo make install')
                    child.expect(['ssword', pexpect.EOF])
                    child.sendline(self.password_e.get_text())
                    #i=child.expect(['Permission denied', pexpect.EOF, timeout=None])
                    child.expect(pexpect.EOF, timeout=None)
                    project_folder_message(child.before)
                    project_folder_message('\n\n')
                    child.close()
                    os.chdir(path)
                    run_again=False
                else:
                    Errorbox('No GNU Radio module found in the given directory. Quitting.')
            elif response == gtk.RESPONSE_REJECT:
                run_again=False
            else:
                self.destroy()
                return response == gtk.RESPONSE_OK
        self.destroy()
        return response == gtk.RESPONSE_OK
	



	

