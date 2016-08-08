# Copyright 2016 Free Software Foundation, Inc.
# This file is part of GNU Radio
#
# GNU Radio Companion is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# GNU Radio Companion is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""
Convert nested data structure from core.ParseXML to output of the yml loader
"""

from .. import Constants


def modify_nested_data(n):
    if n.pop('throttle', ''):
        flags = n.setdefault('flags', '')
        n['flags'] = flags + ' ' + Constants.BLOCK_FLAG_THROTTLE

    # renames
    for name in 'import check callback param sink source'.split():
        n[name + 's'] = n.pop(name, [])
    n['documentation'] = n.pop('doc', '')
    n['value'] = n.pop('var_value', '$value' if n['key'].startswith('variable') else '')
    n['param_tab_order'] = n.get('param_tab_order', {'tab': []})['tab']

    for pn in n['params']:
        pn['dtype'] = pn.pop('type', '')
        category = pn.pop('tab', None)
        if category:
            pn['category'] = category
        pn['options'] = options = pn.pop('option', [])
        for on in options:
            on['value'] = on.pop('key')
            try:
                on['attributes'] = dict(opt.split(':') for opt in on.pop('opt', []))
            except TypeError:
                raise ValueError('Error separating opts into key:value')

    for pn in (n['sinks'] + n['sources']):
        pn['dtype'] = pn.pop('type', '')
        pn['multiplicity'] = pn.pop('nports', '')
        if pn['dtype'] == 'message':
            pn['domain'] = Constants.GR_MESSAGE_DOMAIN
