# Copyright 2015-16 Free Software Foundation, Inc.
# This file is part of GNU Radio
#
# GNU Radio Companion is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# GNU Radio Companion is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

from __future__ import absolute_import

from .block import Block

from .. import utils
from ..Element import Element


class EPyBlock(Block):

    def __init__(self, flow_graph, **kwargs):
        super(EPyBlock, self).__init__(flow_graph, **kwargs)
        self._epy_source_hash = -1  # for epy blocks
        self._epy_reload_error = None

    def rewrite(self):
        Element.rewrite(self)

        param_blk = self.params['_io_cache']
        param_src = self.params['_source_code']

        src = param_src.get_value()
        src_hash = hash((self.name, src))
        if src_hash == self._epy_source_hash:
            return

        try:
            blk_io = utils.epy_block_io.extract(src)

        except Exception as e:
            self._epy_reload_error = ValueError(str(e))
            try:  # Load last working block io
                blk_io_args = eval(param_blk.get_value())
                if len(blk_io_args) == 6:
                    blk_io_args += ([],)  # add empty callbacks
                blk_io = utils.epy_block_io.BlockIO(*blk_io_args)
            except Exception:
                return
        else:
            self._epy_reload_error = None  # Clear previous errors
            param_blk.set_value(repr(tuple(blk_io)))

        # print "Rewriting embedded python block {!r}".format(self.name)

        self._epy_source_hash = src_hash
        self.name = blk_io.name or blk_io.cls
        self._doc = blk_io.doc
        self._imports = ['import ' + self.name]
        self._make = '{0}.{1}({2})'.format(self.name, blk_io.cls, ', '.join(
            '{0}=${{ {0} }}'.format(key) for key, _ in blk_io.params))
        self._callbacks = ['{0} = ${{ {0} }}'.format(attr) for attr in blk_io.callbacks]
        self._update_params(blk_io.params)
        self._update_ports('in', self.sinks, blk_io.sinks, 'sink')
        self._update_ports('out', self.sources, blk_io.sources, 'source')

        super(EPyBlock, self).rewrite()

    def _update_params(self, params_in_src):
        param_factory = self.parent_platform.make_param
        params = {}
        for param in list(self.params):
            if hasattr(param, '__epy_param__'):
                params[param.key] = param
                del self.params[param.key]

        for id_, value in params_in_src:
            try:
                param = params[id_]
                if param.default == param.value:
                    param.set_value(value)
                param.default = str(value)
            except KeyError:  # need to make a new param
                param = param_factory(
                    parent=self,  id=id_, dtype='raw', value=value,
                    name=id_.replace('_', ' ').title(),
                )
                setattr(param, '__epy_param__', True)
            self.params[id_] = param

    def _update_ports(self, label, ports, port_specs, direction):
        port_factory = self.parent_platform.make_port
        ports_to_remove = list(ports)
        iter_ports = iter(ports)
        ports_new = []
        port_current = next(iter_ports, None)
        for key, port_type, vlen in port_specs:
            reuse_port = (
                port_current is not None and
                port_current.dtype == port_type and
                port_current.vlen == vlen and
                (key.isdigit() or port_current.key == key)
            )
            if reuse_port:
                ports_to_remove.remove(port_current)
                port, port_current = port_current, next(iter_ports, None)
            else:
                n = dict(name=label + str(key), dtype=port_type, id=key)
                if port_type == 'message':
                    n['name'] = key
                    n['optional'] = '1'
                if vlen > 1:
                    n['vlen'] = str(vlen)
                port = port_factory(self, direction=direction, **n)
            ports_new.append(port)
        # replace old port list with new one
        del ports[:]
        ports.extend(ports_new)
        # remove excess port connections
        self.parent_flowgraph.disconnect(*ports_to_remove)

    def validate(self):
        super(EPyBlock, self).validate()
        if self._epy_reload_error:
            self.params['_source_code'].add_error_message(str(self._epy_reload_error))
