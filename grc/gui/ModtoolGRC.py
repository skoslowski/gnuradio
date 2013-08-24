import gtk
from gnuradio.modtool import ModToolNewModule, ModTool, ModToolAdd, util_functions, CMakeFileEditor, remove_pattern_from_file, ModToolRemove
import sys
import os
from gnuradio import gr
import re
from optparse import OptionParser, OptionGroup
import glob
from Messages import project_folder_message
from datetime import datetime
#from templates import Templates
#from code_generator import get_template
import Cheetah.Template
from gnuradio.modtool.code_generator import get_template
from gnuradio.modtool.templates import Templates
from gnuradio.modtool.util_functions import append_re_line_sequence

class ModToolException(Exception):
    """ Standard exception for modtool. """
    def __init__(self,arg):
        Errorbox(arg)

class ModToolNewModuleGRC(ModToolNewModule):

    def setup(self,modname,directory):

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

    def setup(self):

        '''(options, self.args) = self.parser.parse_args()
        self.options = options'''
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
		 
        if self._info['version'] == 'autofoo':
            raise ModToolException("Warning: Autotools modules are not supported.Files will be created, but Makefiles will not be edited.")

    def setup_choose_license(self):


        if os.path.isfile('LICENSE'):
            return open('LICENSE').read()
        elif os.path.isfile('LICENCE'):
            return open('LICENCE').read()
        else:
            return Templates['defaultlicense']
    def _run_lib(self):
        """ Do everything that needs doing in the subdir 'lib' and 'include'.
        - add .cc and .h files
        - include them into CMakeLists.txt
        - check if C++ QA code is req'd
        - if yes, create qa_*.{cc,h} and add them to CMakeLists.txt
        """
        def _add_qa():
            " Add C++ QA files for 3.7 API "
            fname_qa_h  = 'qa_%s.h'  % self._info['blockname']
            fname_qa_cc = 'qa_%s.cc' % self._info['blockname']
            self._write_tpl('qa_cpp', 'lib', fname_qa_cc)
            self._write_tpl('qa_h',   'lib', fname_qa_h)
        def _add_qa36():
            " Add C++ QA files for pre-3.7 API (not autotools) "
            fname_qa_cc = 'qa_%s.cc' % self._info['fullblockname']
            self._write_tpl('qa_cpp36', 'lib', fname_qa_cc)

        fname_cc = None
        fname_h  = None
        if self._info['version']  == '37':
            fname_h  = self._info['blockname'] + '.h'
            fname_cc = self._info['blockname'] + '.cc'
            if self._info['blocktype'] in ('source', 'sink', 'sync', 'decimator',
                                           'interpolator', 'general', 'hier', 'tagged_stream'):
                fname_cc = self._info['blockname'] + '_impl.cc'
                self._write_tpl('block_impl_h',   'lib', self._info['blockname'] + '_impl.h')
            self._write_tpl('block_impl_cpp', 'lib', fname_cc)
            self._write_tpl('block_def_h',    self._info['includedir'], fname_h)
        else: # Pre-3.7 or autotools
            fname_h  = self._info['fullblockname'] + '.h'
            fname_cc = self._info['fullblockname'] + '.cc'
            self._write_tpl('block_h36',   self._info['includedir'], fname_h)
            self._write_tpl('block_cpp36', 'lib',                    fname_cc)

        if self._add_cc_qa:
            if self._info['version'] == '37':
                _add_qa()
            elif self._info['version'] == '36':
                _add_qa36()
            elif self._info['version'] == 'autofoo':
                print "Warning: C++ QA files not supported for autotools."

    def _run_swig(self):
        """ Do everything that needs doing in the subdir 'swig'.
        - Edit main *.i file
        """
        if self._get_mainswigfile() is None:
            print 'Warning: No main swig file found.'
            return
        print "Editing %s..." % self._file['swig']
        mod_block_sep = '/'
        if self._info['version'] == '36':
            mod_block_sep = '_'
        swig_block_magic_str = get_template('swig_block_magic', **self._info)
        open(self._file['swig'], 'a').write(swig_block_magic_str)
        include_str = '#include "%s%s%s.h"' % (
                self._info['modname'],
                mod_block_sep,
                self._info['blockname'])
        if re.search('#include', open(self._file['swig'], 'r').read()):
            append_re_line_sequence(self._file['swig'], '^#include.*\n', include_str)
        else: # I.e., if the swig file is empty
            oldfile = open(self._file['swig'], 'r').read()
            regexp = re.compile('^%\{\n', re.MULTILINE)
            oldfile = regexp.sub('%%{\n%s\n' % include_str, oldfile, count=1)
            open(self._file['swig'], 'w').write(oldfile)

    def _run_python_qa(self):
        """ Do everything that needs doing in the subdir 'python' to add
        QA code.
        - add .py files
        - include in CMakeLists.txt
        """
        fname_py_qa = 'qa_' + self._info['blockname'] + '.py'
        self._write_tpl('qa_python', 'python', fname_py_qa)
        os.chmod(os.path.join('python', fname_py_qa), 0755)

        print "Editing python/CMakeLists.txt..."
        open(self._file['cmpython'], 'a').write(
                'GR_ADD_TEST(qa_%s ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/%s)\n' % \
                  (self._info['blockname'], fname_py_qa))

    def _run_python(self):
        """ Do everything that needs doing in the subdir 'python' to add
        a Python block.
        - add .py file
        - include in CMakeLists.txt
        - include in __init__.py
        """
        fname_py = self._info['blockname'] + '.py'
        self._write_tpl('block_python', 'python', fname_py)
        append_re_line_sequence(self._file['pyinit'],
                                '(^from.*import.*\n|# import any pure.*\n)',
                                'from %s import %s' % (self._info['blockname'], self._info['blockname']))

        ed = CMakeFileEditor(self._file['cmpython'])
        ed.append_value('GR_PYTHON_INSTALL', fname_py, to_ignore_end='DESTINATION[^()]+')
        ed.write()

    def _run_grc(self):
        """ Do everything that needs doing in the subdir 'grc' to add
        a GRC bindings XML file.
        - add .xml file
        - include in CMakeLists.txt
        """
        fname_grc = self._info['fullblockname'] + '.xml'
        self._write_tpl('grc_xml', 'grc', fname_grc)
        ed = CMakeFileEditor(self._file['cmgrc'], '\n    ')

        print "Editing grc/CMakeLists.txt..."
        ed.append_value('install', fname_grc, to_ignore_end='DESTINATION[^()]+')
        ed.write()


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


    '''def _run_subdir(self, path, globs, makefile_vars, cmakeedit_func=None):

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
        return files_deleted'''



def Errorbox(err_msg): 
    message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
    message.set_markup(err_msg)
    message.run()
    message.destroy()
