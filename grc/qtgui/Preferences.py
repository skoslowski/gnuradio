"""
Copyright 2008 Free Software Foundation, Inc.
This file is part of GNU Radio

GNU Radio Companion is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

GNU Radio Companion is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

import ConfigParser
import os
from base64 import b64encode, b64decode

_platform = None
_config_parser = ConfigParser.ConfigParser()

def file_extension():
    return '.grcqt' #.'+  _platform.get_key()
def _prefs_file():
    return os.path.join(os.path.expanduser('~'), file_extension())

def load(platform):
    global _platform
    _platform = platform
    #create sections
    _config_parser.add_section('main')
    _config_parser.add_section('files_open')
    try:
        _config_parser.read(_prefs_file())
    except:
        pass

def save():
    try:
        _config_parser.write(open(_prefs_file(), 'w'))
    except:
        pass

###########################################################################
# Special methods for specific program functionalities
###########################################################################

def main_window_state(state=None):
    if state is not None:
        #ToDo: Ugly b64
        _config_parser.set('main', 'main_window_state', b64encode(state))
    else:
        try:
            return b64decode(_config_parser.get('main', 'main_window_state'))
        except:
            return None

def main_window_geometry(geometry=None):
    if geometry is not None:
        #ToDo: Ugly b64
        _config_parser.set('main', 'main_window_geometry', b64encode(geometry))
    else:
        try:
            return b64decode(_config_parser.get('main', 'main_window_geometry'))
        except:
            return None


def file_open(file=None):
    if file is not None:
        _config_parser.set('main', 'file_open', file)
    else:
        try:
            return _config_parser.get('main', 'file_open')
        except:
            return ''

def files_open(files=None):
    if files is not None:
        _config_parser.remove_section('files_open') #clear section
        _config_parser.add_section('files_open')
        for i, file in enumerate(files):
            _config_parser.set('files_open', 'file_open_%d' % i, file)
    else:
        files = list()
        i = 0
        while True:
            try:
                files.append(_config_parser.get('files_open', 'file_open_%d'%i))
            except:
                return files
            i += 1
