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
import os
import subprocess
import shlex

from distutils.spawn import find_executable as distutils_find_executable
from .. python.Constants import XTERM_EXECUTABLE
XTERM_EXECUTABLE = distutils_find_executable(XTERM_EXECUTABLE)


def start_process_local(target, try_xterm):
    """
    Execute python flow graph.

    Args:
        target: file path of the generated flow graph
        try_xterm: attempt to start a graphical terminal

    Returns:
        a popen object
    """
    # extract the path to the python executable
    args = [sys.executable, '-u', target]  # -u is unbuffered stdio
    # when in no gui mode on linux, use a graphical terminal (looks nice)
    if try_xterm and XTERM_EXECUTABLE:
        args = [XTERM_EXECUTABLE, '-e'] + args

    return subprocess.Popen(args,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True
    )


# from package 'execnet': this will receive and run the bootstrap code below
REMOTE_COMMAND = "{0} 'import sys;exec(eval(sys.stdin.readline()))'"
REMOTE_BOOTSTRAP_CODE_TEMPLATE = """
import sys
import runpy

with open({name!r}, "wb") as fp:
    fp.write(sys.stdin.read({size}))

sys.path.insert(0, {name!r})
runpy.run_module("__main__", run_name="__main__")
"""


def start_process_remote(target, try_xterm, hostname, ssh_cmd='', run_cmd=''):
    """
    Execute python flow graph on a remote machine

    Args:
        target: file path of the generated flow graph
        try_xterm: attempt to start a graphical terminal
        host: [user@]hostname argument for ssh
        ssh_cmd: command to use instead of 'ssh', e.g.

    Returns:
        a popen object
    """
    args = shlex.split(ssh_cmd) if ssh_cmd else ["ssh"]
    args += [hostname, REMOTE_COMMAND.format(run_cmd or 'python2 -uc')]
    if try_xterm and XTERM_EXECUTABLE:
        args = [XTERM_EXECUTABLE, '-e'] + args

    process = subprocess.Popen(args,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, universal_newlines=True
    )
    try:
        with open(target, 'rb') as fp:
            # get file size
            fp.seek(0, os.SEEK_END)
            target_size = fp.tell()
            fp.seek(0, os.SEEK_SET)
            # send bootstrap code
            process.stdin.write((repr(
                REMOTE_BOOTSTRAP_CODE_TEMPLATE.format(
                    size=target_size, name=os.path.basename(target))
            ) + '\n').encode('ascii'))
            # send target file
            process.stdin.write(fp.read())
            process.stdin.flush()
    except IOError:
        process.kill()  # process output printed in run

    return process
