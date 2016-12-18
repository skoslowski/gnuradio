# Copyright 2008-2016 Free Software Foundation, Inc.
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

from . import _virtual_connections

from .. import Constants
from ..Element import Element, lazy_property
from ..eval import Evaluated, EvaluatedEnum, EvaluatedPInt


class Port(Element):

    is_port = True

    dtype = EvaluatedEnum(list(Constants.TYPE_TO_SIZEOF.keys()), default='', name='dtype')
    vlen = EvaluatedPInt(name='vlen')
    multiplicity = EvaluatedPInt(name='multiplicity')
    hidden = Evaluated((bool, int), default=False, name='hidden')
    optional = Evaluated((bool, int), default=False, name='optional')

    def __init__(self, parent, direction, id, label='', domain=Constants.DEFAULT_DOMAIN, dtype='',
                 vlen='', multiplicity=1, optional=False, hide='', **_):
        """Make a new port from nested data."""
        Element.__init__(self, parent)

        self._dir = direction
        self.key = id
        if not label:
            label = id if not id.isdigit() else {'sink': 'in', 'source': 'out'}[direction] + id
        self.name = self._base_name = label

        self.domain = domain
        self.dtype = dtype
        self.vlen = vlen

        if domain == Constants.GR_MESSAGE_DOMAIN:  # ToDo: message port class
            self.key = self.name
            self.dtype = 'message'

        self.multiplicity = multiplicity
        self.optional = optional
        self.hidden = hide
        # end of args ########################################################
        self.clones = []  # References to cloned ports (for nports > 1)

    def __str__(self):
        if self.is_source:
            return 'Source - {}({})'.format(self.name, self.key)
        if self.is_sink:
            return 'Sink - {}({})'.format(self.name, self.key)

    def __repr__(self):
        return '{!r}.{}[{}]'.format(self.parent, 'sinks' if self.is_sink else 'sources', self.key)

    @property
    def item_size(self):
        return Constants.TYPE_TO_SIZEOF[self.dtype] * self.vlen

    @lazy_property
    def is_sink(self):
        return self._dir == 'sink'

    @lazy_property
    def is_source(self):
        return self._dir == 'source'

    @property
    def inherit_type(self):
        """always empty for e.g. virtual blocks, may eval to empty for 'Wildcard'"""
        return not self.dtype

    def validate(self):
        Element.validate(self)
        platform = self.parent_platform

        num_connections = len(list(self.connections(enabled=True)))
        need_connection = not self.optional and not self.hidden
        if need_connection and num_connections == 0:
            self.add_error_message('Port is not connected.')

        if self.dtype not in Constants.TYPE_TO_SIZEOF.keys():
            self.add_error_message('Type "{}" is not a possible type.'.format(self.dtype))

        try:
            domain = platform.domains[self.domain]
            if self.is_sink and not domain.multi_in and num_connections > 1:
                self.add_error_message('Domain "{}" can have only one upstream block'
                                       ''.format(self.domain))
            if self.is_source and not domain.multi_out and num_connections > 1:
                self.add_error_message('Domain "{}" can have only one downstream block'
                                       ''.format(self.domain))
        except KeyError:
            self.add_error_message('Domain key "{}" is not registered.'.format(self.domain))

    def rewrite(self):
        del self.vlen
        del self.multiplicity
        del self.hidden
        del self.optional
        del self.dtype

        if self.inherit_type:
            self.resolve_empty_type()

        Element.rewrite(self)

        # Update domain if was deduced from (dynamic) port type
        if self.domain == Constants.GR_STREAM_DOMAIN and self.dtype == "message":
            self.domain = Constants.GR_MESSAGE_DOMAIN
            self.key = self.name
        if self.domain == Constants.GR_MESSAGE_DOMAIN and self.dtype != "message":
            self.domain = Constants.GR_STREAM_DOMAIN
            self.key = '0'  # Is rectified in rewrite()

    def resolve_virtual_source(self):
        """Only used by Generator after validation is passed"""
        return _virtual_connections.upstream_ports(self)

    def resolve_empty_type(self):
        def find_port(finder):
            try:
                return next((p for p in finder(self) if not p.inherit_type), None)
            except _virtual_connections.LoopError as error:
                self.add_error_message(str(error))
            except (StopIteration, Exception):
                pass

        try:
            port = find_port(_virtual_connections.upstream_ports) or \
                   find_port(_virtual_connections.downstream_ports)
            self.set_evaluated('dtype', port.dtype)  # we don't want to override the template
            self.set_evaluated('vlen', port.vlen)  # we don't want to override the template
            self.domain = port.domain
        except AttributeError:
            self.domain = Constants.DEFAULT_DOMAIN

    def add_clone(self):
        """
        Create a clone of this (master) port and store a reference in self._clones.

        The new port name (and key for message ports) will have index 1... appended.
        If this is the first clone, this (master) port will get a 0 appended to its name (and key)

        Returns:
            the cloned port
        """
        # Add index to master port name if there are no clones yet
        if not self.clones:
            self.name = self._base_name + '0'
            # Also update key for none stream ports
            if not self.key.isdigit():
                self.key = self.name

        name = self._base_name + str(len(self.clones) + 1)
        # Dummy value 99999 will be fixed later
        key = '99999' if self.key.isdigit() else name

        # Clone
        port_factory = self.parent_platform.make_port
        port = port_factory(self.parent, direction=self._dir,
                            name=name, key=key,
                            master=self, cls_key='clone')

        self.clones.append(port)
        return port

    def remove_clone(self, port):
        """
        Remove a cloned port (from the list of clones only)
        Remove the index 0 of the master port name (and key9 if there are no more clones left
        """
        self.clones.remove(port)
        # Remove index from master port name if there are no more clones
        if not self.clones:
            self.name = self._base_name
            # Also update key for none stream ports
            if not self.key.isdigit():
                self.key = self.name

    def connections(self, enabled=None):
        """Iterator over all connections to/from this port

        enabled: None for all, True for enabled only, False for disabled only
        """
        for con in self.parent_flowgraph.connections:
            if self in con and (enabled is None or enabled == con.enabled):
                yield con
