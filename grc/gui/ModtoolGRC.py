import gtk
from gnuradio.modtool import ModToolNewModule, ModTool, ModToolAdd, util_functions, CMakeFileEditor, remove_pattern_from_file, ModToolRemove
import sys
import os
from gnuradio import gr
import re
from optparse import OptionParser, OptionGroup
import glob
from Messages import project_folder_message

class ModToolException(Exception):
    """ Standard exception for modtool. """
    def __init__(self,arg):
        Errorbox(arg)

class ModToolNewModuleGRC(ModToolNewModule):

    def setup(self,modname,directory):

        self._info['modname'] = modname
        if not re.match('[a-zA-Z0-9_]+', self._info['modname']):
            '''Errorbox('Invalid module name.')'''
            try:
                raise ModToolException('Invalid module name.')
            except ModToolException:
                return False
        if not os.path.isdir(directory):
            Errorbox('Could not find the dir %s.' % directory)
            return False
        self._dir = '%s/gr-%s' % (directory,self._info['modname'])
        try:
            os.stat(self._dir)
        except OSError:
            pass # This is what should happen
        else:
            Errorbox('The given directory exists.')
            return False
        self._srcdir = gr.prefs().get_string('modtool', 'newmod_path', '/usr/local/share/gnuradio/modtool/gr-newmod')
        if not os.path.isdir(self._srcdir):
            Errorbox('Could not find gr-newmod source dir.')
            return False
        return True

class ModToolGRC(ModTool):

    def setup(self):

        (options, self.args) = self.parser.parse_args()
        self.options = options
        self._dir = self.directory
	print self._dir
        print self._check_directory(self._dir)
        if not self._check_directory(self._dir):
            Errorbox("No GNU Radio module found in the given directory. Quitting.")
            return False
        self._info['modname'] = self.modname
        if self._info['modname'] is None:
            Errorbox("No GNU Radio module found in the given directory. Quitting.")
            return False
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
        self._info['yes'] = options.yes

class ModToolAddGRC(ModToolAdd,ModToolGRC):

    def __init__(self,directory, modname, blocktype, blockname, arg):
        ModTool.__init__(self)
        self.directory=directory
        self.modname=modname
        self.blocktype=blocktype
        self.blockname=blockname
        self.arg=arg
        self._add_cc_qa = False
        self._add_py_qa = False

    def setup(self):


        ModToolGRC.setup(self)
        self._info['modname']=self.modname
        self._info['blocktype'] = self.blocktype
        self._info['lang'] = 'cpp'
        if self._info['lang'] == 'c++':
            self._info['lang'] = 'cpp'


        if ((self._skip_subdirs['lib'] and self._info['lang'] == 'cpp')
		     or (self._skip_subdirs['python'] and self._info['lang'] == 'python')):
            Errorbox("Missing or skipping relevant subdir.")
            return False

        self._info['blockname']=self.blockname
		
        if not re.match('[a-zA-Z0-9_]+', self._info['blockname']):
            Errorbox('Invalid block name.')
            return False

        self._info['fullblockname'] = self._info['modname'] + '_' + self._info['blockname']
        self._info['license'] = self.setup_choose_license()
        self._info['arglist'] = self.arg
		
        if not (self._info['blocktype'] in ('noblock') or self._skip_subdirs['python']):
            self._add_py_qa = False
        if self._info['lang'] == 'cpp' :
            self._add_cc_qa = False 
		 
        if self._info['version'] == 'autofoo':
            Errorbox("Warning: Autotools modules are not supported.Files will be created, but Makefiles will not be edited.")
        return True



class ModToolRemoveGRC(ModToolRemove,ModToolGRC):

    def __init__(self, lib, include, swig, grc, python,modname,blockname,directory):
        ModTool.__init__(self)
        self.lib=lib
        self.include=include
        self.swig=swig
        self.python=python
        self.grc=grc
        self.directory=directory
        self.blockname=blockname
        self.modname=modname
        

    def setup(self):

        ModToolGRC.setup(self)
        self._info['modname']=self.modname
        self._info['pattern'] =self.blockname
        if len(self._info['pattern']) == 0:
            self._info['pattern'] = '.'
    def _run_subdir(self, path, globs, makefile_vars, cmakeedit_func=None):

        files = []
        for g in globs:
            files = files + glob.glob("%s/%s"% (path, g))
        files_filt = []
        print "Searching for matching files in %s/:" % path
        for f in files:
            if re.search(self._info['pattern'], os.path.basename(f)) is not None:
                files_filt.append(f)
        if len(files_filt) == 0:
            print "None found."
            if ((self.lib is True and 'lib' in path.lower()) or (self.include is True and 'include' in path.lower()) or (self.swig is True and 'swig' in path.lower()) or (self.python is True and 'python' in path.lower()) or (self.grc is True and 'grc' in path.lower())):
                project_folder_message('Files are not found in "%s".\n' %path)
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
            project_folder_message('Deleting "%s".\n' % f)
            os.unlink(f)
            print "Deleting occurrences of %s from %s/CMakeLists.txt..." % (b, path)
            for var in makefile_vars:
                ed.remove_value(var, b)
            if cmakeedit_func is not None:
                cmakeedit_func(b, ed)
        ed.write()
        return files_deleted



def Errorbox(err_msg): 
    message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
    message.set_markup(err_msg)
    message.run()
    message.destroy()
