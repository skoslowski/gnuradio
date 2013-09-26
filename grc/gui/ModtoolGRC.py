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
import gtk
from gnuradio.modtool import ModToolNewModule, ModTool, ModToolAdd, util_functions, CMakeFileEditor, remove_pattern_from_file, ModToolRemove
import sys
import os
from gnuradio import gr
import re
from optparse import OptionParser, OptionGroup
import glob
from Messages import OTM_message
from datetime import datetime
import Cheetah.Template
from gnuradio.modtool.code_generator import get_template
from gnuradio.modtool.templates import Templates
from gnuradio.modtool.util_functions import append_re_line_sequence

class ModToolException(Exception):
    """ Standard exception for modtool. """
    def __init__(self,arg):
        Errorbox(arg)

class ModToolNewModuleGRC(ModToolNewModule):
  
    """sub class of ModToolNewModule"""

    def setup(self,modname,directory):

        """override the setup function of original module"""

        self._info['modname'] = modname
        if not re.match('[a-zA-Z0-9_]+', self._info['modname']):
            raise ModToolException('Invalid module name.')
        if not os.path.isdir(directory):
            raise ModToolException('Could not find the dir %s.' % directory)
        self._dir = '%s/gr-%s' % (directory,self._info['modname'])
        try:
            os.stat(self._dir)
        except OSError:
            pass # This is what should happen
        else:
            raise ModToolException('The given directory exists.')
        self._srcdir = gr.prefs().get_string('modtool', 'newmod_path', '/usr/local/share/gnuradio/modtool/gr-newmod')
        if not os.path.isdir(self._srcdir):
            raise ModToolException('Could not find gr-newmod source dir.')


class ModToolGRC(ModTool):

    """sub class of ModTool"""

    def setup(self):

        """override the setup function of original module"""

        self._dir = self.directory
        if not self._check_directory(self._dir):
            raise ModToolException("No GNU Radio module found in the given directory. Quitting.")
        self._info['modname'] = self.modname
        if self._info['modname'] is None:
            raise ModToolException("No GNU Radio module found in the given directory. Quitting.")
        print "GNU Radio module name identified: " + self._info['modname']
        if self._info['version'] == '36' and os.path.isdir(os.path.join('include', self._info['modname'])):
            self._info['version'] = '37'
        if not self._has_subdirs['lib']:
            self._skip_subdirs['lib'] = True
        if not self._has_subdirs['python']:
            self._skip_subdirs['python'] = True
        if self._get_mainswigfile() is None or not self._has_subdirs['swig']:
            self._skip_subdirs['swig'] = True
        if not self._has_subdirs['grc']:
            self._skip_subdirs['grc'] = True
        self._info['blockname'] = self.blockname
        self._setup_files()
        self._info['yes'] = 'yes'

class ModToolAddGRC(ModToolAdd,ModToolGRC):

    """sub class of ModToolAdd"""

    def __init__(self,directory, modname, blocktype, blockname, arg):
        ModTool.__init__(self)
        self.directory=directory
        self.modname=modname
        self.blocktype=blocktype
        self.blockname=blockname
        self.arg=arg
        self._add_cc_qa = False
        self._add_py_qa = False
        self._skip_cmakefiles = False
        self._license_file = None

    def setup(self):

        """override the setup function of original module"""

        ModToolGRC.setup(self)
        self._info['modname']=self.modname
        self._info['blocktype'] = self.blocktype
        self._info['lang'] = 'cpp'
        if self._info['lang'] == 'c++':
            self._info['lang'] = 'cpp'


        if ((self._skip_subdirs['lib'] and self._info['lang'] == 'cpp')
		     or (self._skip_subdirs['python'] and self._info['lang'] == 'python')):
            raise ModToolException("Missing or skipping relevant subdir.")

        self._info['blockname']=self.blockname
		
        if not re.match('[a-zA-Z0-9_]+', self._info['blockname']):
            raise ModToolException('Invalid block name.')

        self._info['fullblockname'] = self._info['modname'] + '_' + self._info['blockname']
        self._info['license'] = self.setup_choose_license()
        self._info['arglist'] = self.arg
		
        if not (self._info['blocktype'] in ('noblock') or self._skip_subdirs['python']):
            self._add_py_qa = False
        if self._info['lang'] == 'cpp' :
            self._add_cc_qa = False 

        if self._info['version'] == 'autofoo' and not self._skip_cmakefiles:
            print "Warning: Autotools modules are not supported. ",
            print "Files will be created, but Makefiles will not be edited."
            self._skip_cmakefiles = True
		 


class ModToolRemoveGRC(ModToolRemove,ModToolGRC):

    """sub class of ModToolRemove"""

    def __init__(self, modname,blockname,directory):
        ModTool.__init__(self)
        self.directory=directory
        self.blockname=blockname
        self.modname=modname
        

    def setup(self):

        """override the setup function of original module"""

        ModToolGRC.setup(self)
        self._info['modname']=self.modname
        self._info['pattern'] =self.blockname
        if len(self._info['pattern']) == 0:
            self._info['pattern'] = '.'





def Errorbox(err_msg): 
    message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
    message.set_markup(err_msg)
    message.run()
    message.destroy()
