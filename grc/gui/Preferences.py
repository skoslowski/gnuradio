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
from collections import namedtuple

_platform = None
_config_parser = ConfigParser.ConfigParser()


def file_extension(): return '.'+_platform.get_key()


def load(platform):
    global _platform
    _platform = platform
    _config_parser.add_section('main')
    _config_parser.add_section('files_open')
    try:
        _config_parser.read(_platform.get_prefs_file())
    except:
        pass


DISCLAIMER = """\
# Warning: Except for the section 'remote_servers' all entries are overwritten
#          when closing GRC. Extra entries and comments are not preserved.
#
# To add servers for remote execution, add entries like the following to the
# section 'remote_servers'.
#
#     NAME = HOSTNAME                          ; the hostname argument for ssh
#     NAME_hostname = HOSTNAME                 ; same as 'NAME = ' only
#     NAME_label = LABEL_IN_THE_MENU           ; defaults to NAME_host
#     NAME_ssh_cmd = CUSTOM_SSH_COMMAND        ; defaults to 'ssh'
#     NAME_run_cmd = CUSTOM_COMMAND_ON_REMOTE  ; defaults to 'python2 -uc'
#
# where NAME is a unique string. The resulting command line is
#
#     CUSTOM_SSH_COMMAND HOSTNAME CUSTOM_COMMAND_ON_REMOTE '...'
#     ssh my_host python2 -uc '...'
#
# If you opened this file from grc (and are on posix) your changes are applied
# when the editor is closed, else restart GRC to see your changes.
#
# Note, ssh will try to call ssh-askpass if you need to enter password. Make
# sure hostname is in the list of known hosts. Instead of a custom ssh command
# (custom port, ...) it might be simpler to add an entry to your ssh_config.

"""

def save():
    try:
        reload_remote_servers()
        with open(_platform.get_prefs_file(), 'w') as fp:
            fp.write(DISCLAIMER)
            _config_parser.write(fp)
    except:
        pass


def reload_remote_servers():
    try:
        # reload server list before rewriting the prefs file
        cp = ConfigParser.ConfigParser()
        cp.read(_platform.get_prefs_file())
        server_params = remote_servers(config_parser=cp)
        remote_servers(server_params)
    except:
        return False
    return True

###########################################################################
# Special methods for specific program functionalities
###########################################################################

def main_window_size(size=None):
    if size is not None:
        _config_parser.set('main', 'main_window_width', size[0])
        _config_parser.set('main', 'main_window_height', size[1])
    else:
        try:
            return (
                _config_parser.getint('main', 'main_window_width'),
                _config_parser.getint('main', 'main_window_height'),
            )
        except ConfigParser.Error:
            return 1, 1


def file_open(file=None):
    if file is not None:
        _config_parser.set('main', 'file_open', file)
    else:
        try:
            return _config_parser.get('main', 'file_open')
        except ConfigParser.Error:
            return ''


def files_open(files=None):
    if files is not None:
        _config_parser.remove_section('files_open') #clear section
        _config_parser.add_section('files_open')
        for i, file in enumerate(files):
            _config_parser.set('files_open', 'file_open_%d'%i, file)
    else:
        files = list()
        i = 0
        while True:
            try:
                files.append(_config_parser.get('files_open', 'file_open_%d'%i))
            except ConfigParser.Error:
                return files
            i += 1


def reports_window_position(pos=None):
    if pos is not None:
        _config_parser.set('main', 'reports_window_position', pos)
    else:
        try:
            return _config_parser.getint('main', 'reports_window_position') or 1 #greater than 0
        except ConfigParser.Error:
            return -1


def blocks_window_position(pos=None):
    if pos is not None:
        _config_parser.set('main', 'blocks_window_position', pos)
    else:
        try:
            return _config_parser.getint('main', 'blocks_window_position') or 1 #greater than 0
        except ConfigParser.Error:
            return -1


def bool_entry(key, active=None, default=True):
    if active is not None:
        _config_parser.set('main', key, active)
    else:
        try:
            return _config_parser.getboolean('main', key)
        except ConfigParser.Error:
            return default


RemoteServerParams = namedtuple("RemoteServers",
                                "hostname label ssh_cmd run_cmd key")


def remote_servers(server_params=None, config_parser=_config_parser):
    if server_params is not None:
        if config_parser.has_section("remote_servers"):  # clean-out list
            config_parser.remove_section("remote_servers")
        config_parser.add_section('remote_servers')
        make_option = lambda l: "{0}_{1}".format(target.key, l)
        for target in map(lambda t: RemoteServerParams(*t), server_params):
            config_parser.set('remote_servers', make_option('hostname'), target.hostname)
            if target.label and target.label != target.hostname:
                config_parser.set('remote_servers', make_option('label'), target.label)
            if target.ssh_cmd:
                config_parser.set('remote_servers', make_option('ssh_cmd'), target.ssh_cmd)
            if target.run_cmd:
                config_parser.set('remote_servers', make_option('run_cmd'), target.run_cmd)
    else:
        keys, options = list(), dict()
        if config_parser.has_section("remote_servers"):
            for name, value in config_parser.items("remote_servers"):
                key, _, option = name.partition('_')
                if key not in keys:  # ordered-default-dict
                    keys.append(key)  # preserve order
                    options[key] = dict()  # set default
                options[key][option] = value
        server_params = list()
        for key, params in map(lambda k: (k, options[k]), keys):
            try:
                hostname = params.get('') or params['hostname']
                assert hostname and ' ' not in hostname
                server_params.append(RemoteServerParams(
                    hostname=hostname,
                    label=params.get('label', hostname),
                    ssh_cmd=params.get('ssh_cmd', ''),
                    run_cmd=params.get('run_cmd', ''),
                    key=key
                ))
            except (KeyError, AssertionError):
                continue
        return server_params
