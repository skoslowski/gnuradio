"""
Copyright 2015 Free Software Foundation, Inc.
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

import sys
import subprocess
from distutils.spawn import find_executable as distutils_find_executable

from .. python.Constants import XTERM_EXECUTABLE
XTERM_EXECUTABLE = distutils_find_executable(XTERM_EXECUTABLE)


def start_process_local(target, try_xterm):
    """
    Execute python flow graph.

    Returns:
        a popen object
    """

    # extract the path to the python executable
    python_exe = sys.executable

    # setup the command args to run
    cmds = [python_exe, '-u', target]  # -u is unbuffered stdio

    # when in no gui mode on linux, use a graphical terminal (looks nice)
    if try_xterm and XTERM_EXECUTABLE:
        cmds = [XTERM_EXECUTABLE, '-e'] + cmds

    return subprocess.Popen(
        args=cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        shell=False, universal_newlines=True)
