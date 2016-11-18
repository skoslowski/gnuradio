"""
Copyright 2008-2017 Free Software Foundation, Inc.
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

from __future__ import absolute_import

from itertools import chain

from six.moves import filter

from . import Constants
from .Element import Element, lazy_property
from .eval import Evaluated, EvaluatedEnum, EvaluatedPInt


class LoopError(Exception):
    pass


def _upstream_ports(port):
    if port.is_sink:
        return _sources_from_virtual_sink_port(port)
    else:
        return _sources_from_virtual_source_port(port)


def _sources_from_virtual_sink_port(sink_port, _traversed=None):
    """
    Resolve the source port that is connected to the given virtual sink port.
    Use the get source from virtual source to recursively resolve subsequent ports.
    """
    source_ports_per_virtual_connection = (
        # there can be multiple ports per virtual connection
        _sources_from_virtual_source_port(c.source_port, _traversed)  # type: list
        for c in sink_port.get_enabled_connections()
    )
    return list(chain(*source_ports_per_virtual_connection))  # concatenate generated lists of ports


def _sources_from_virtual_source_port(source_port, _traversed=None):
    """
    Recursively resolve source ports over the virtual connections.
    Keep track of traversed sources to avoid recursive loops.
    """
    _traversed = set(_traversed or [])  # a new set!
    if source_port in _traversed:
        raise LoopError('Loop found when resolving port type')
    _traversed.add(source_port)

    block = source_port.parent_block
    flow_graph = source_port.parent_flow_graph

    if not block.is_virtual_source():
        return [source_port]  # nothing to resolve, we're done

    stream_id = block.get_param('stream_id').get_value()

    # currently the validation does not allow multiple virtual sinks and one virtual source
    # but in the future it may...
    connected_virtual_sink_blocks = (
        b for b in flow_graph.iter_enabled_blocks()
        if b.is_virtual_sink() and b.params['stream_id'].get_value() == stream_id
    )
    source_ports_per_virtual_connection = (
        _sources_from_virtual_sink_port(b.sinks[0], _traversed)  # type: list
        for b in connected_virtual_sink_blocks
    )
    return list(chain(*source_ports_per_virtual_connection))  # concatenate generated lists of ports


def _downstream_ports(port):
    if port.is_source:
        return _sinks_from_virtual_source_port(port)
    else:
        return _sinks_from_virtual_sink_port(port)


def _sinks_from_virtual_source_port(source_port, _traversed=None):
    """
    Resolve the sink port that is connected to the given virtual source port.
    Use the get sink from virtual sink to recursively resolve subsequent ports.
    """
    sink_ports_per_virtual_connection = (
        # there can be multiple ports per virtual connection
        _sinks_from_virtual_sink_port(c.sink_port, _traversed)  # type: list
        for c in source_port.get_enabled_connections()
    )
    return list(chain(*sink_ports_per_virtual_connection))  # concatenate generated lists of ports


def _sinks_from_virtual_sink_port(sink_port, _traversed=None):
    """
    Recursively resolve sink ports over the virtual connections.
    Keep track of traversed sinks to avoid recursive loops.
    """
    _traversed = set(_traversed or [])  # a new set!
    if sink_port in _traversed:
        raise LoopError('Loop found when resolving port type')
    _traversed.add(sink_port)

    block = sink_port.parent_block
    flow_graph = sink_port.parent_flow_graph

    if not block.is_virtual_sink():
        return [sink_port]

    stream_id = block.get_param('stream_id').get_value()

    connected_virtual_source_blocks = (
        b for b in flow_graph.iter_enabled_blocks()
        if b.is_virtual_source() and b.params['stream_id'].get_value() == stream_id
    )
    sink_ports_per_virtual_connection = (
        _sinks_from_virtual_source_port(b.sources[0], _traversed)  # type: list
        for b in connected_virtual_source_blocks
    )
    return list(chain(*sink_ports_per_virtual_connection))  # concatenate generated lists of ports


class Port(Element):

    is_port = True
    is_clone = False

    dtype = EvaluatedEnum(Constants.TYPE_TO_SIZEOF.keys(), default='complex', name='dtype')
    vlen = EvaluatedPInt(name='vlen')
    multiplicity = EvaluatedPInt(name='multiplicity')
    hidden = Evaluated((bool, int), default=False, name='hidden')
    optional = Evaluated((bool, int), default=False, name='optional')

    def __init__(self, parent, direction, id, label='', domain=Constants.DEFAULT_DOMAIN, dtype='complex',
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

        self.inherit_type = not dtype
        self.clones = []  # References to cloned ports (for nports > 1)

    def __str__(self):
        if self.is_source:
            return 'Source - {}({})'.format(self.name, self.key)
        if self.is_sink:
            return 'Sink - {}({})'.format(self.name, self.key)

    def __repr__(self):
        return '{!r}.{}[{}]'.format(self.parent, 'sinks' if self.is_sink else 'sources', self.key)

    def validate(self):
        Element.validate(self)
        platform = self.parent_platform
        if self.domain not in platform.domains:
            self.add_error_message('Domain key "{}" is not registered.'.format(self.domain))
        if not self.get_enabled_connections() and not self.optional:
            self.add_error_message('Port is not connected.')
        if self.dtype not in Constants.TYPE_TO_SIZEOF.keys():
            self.add_error_message('Type "{}" is not a possible type.'.format(self.dtype))

    def rewrite(self):
        """
        Handle the port cloning for virtual blocks.
        """
        del self.vlen
        del self.multiplicity
        del self.hidden
        del self.optional
        del self.dtype

        if self.inherit_type:
            try:
                # Clone type and vlen
                source = self.resolve_empty_type()
                self.dtype = source.dtype
                self.vlen = source.vlen
            except:
                pass

        Element.rewrite(self)

        # Update domain if was deduced from (dynamic) port type
        type_ = self.dtype
        if self.domain == Constants.GR_STREAM_DOMAIN and type_ == "message":
            self.domain = Constants.GR_MESSAGE_DOMAIN
            self.key = self.name
        if self.domain == Constants.GR_MESSAGE_DOMAIN and type_ != "message":
            self.domain = Constants.GR_STREAM_DOMAIN
            self.key = '0'  # Is rectified in rewrite()

    def resolve_virtual_source(self):
        """Only used by Generator after validation is passed"""
        return _upstream_ports(self)

    def resolve_empty_type(self):
        def find_port(finder):
            try:
                return next((p for p in finder(self) if not p.inherit_type), None)
            except LoopError as error:
                self.add_error_message(str(error))
            except (StopIteration, Exception) as error:
                pass

        try:
            port = find_port(_upstream_ports) or find_port(_downstream_ports)
            self._type = str(port.get_type())
            self._vlen = str(port.get_vlen())
        except Exception:
            # Reset type and vlen
            self._type = self._vlen = ''

    @property
    def item_size(self):
        return Constants.TYPE_TO_SIZEOF[self.dtype] * self.vlen

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
        port_factory = self.parent_platform.get_new_port
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

    @lazy_property
    def is_sink(self):
        return self._dir == 'sink'

    @lazy_property
    def is_source(self):
        return self._dir == 'source'

    def get_connections(self):
        """
        Get all connections that use this port.

        Returns:
            a list of connection objects
        """
        connections = self.parent_flowgraph.connections
        return [c for c in connections if c.source_port is self or c.sink_port is self]

    def get_enabled_connections(self):
        """
        Get all enabled connections that use this port.

        Returns:
            a list of connection objects
        """
        return [c for c in self.get_connections() if c.enabled]

    def get_associated_ports(self):
        if not self.dtype == 'bus':
            return [self]

        block = self.parent_block
        if self.is_source:
            block_ports = block.sources
            bus_structure = block.current_bus_structure['source']
        else:
            block_ports = block.sinks
            bus_structure = block.current_bus_structure['sink']

        ports = [i for i in block_ports if not i.dtype == 'bus']
        if bus_structure:
            bus_index = [i for i in block_ports if i.dtype == 'bus'].index(self)
            ports = [p for i, p in enumerate(ports) if i in bus_structure[bus_index]]
        return ports


class PortClone(Port):

    is_clone = True

    def __init__(self, parent, direction, master, name, key):
        """
        Make a new port from nested data.

        Args:
            block: the parent element
            n: the nested odict
            dir: the direction
        """
        Element.__init__(self, parent)
        self.master = master
        self.name = name
        self._key = key
        self.multiplicity = 1

    def __getattr__(self, item):
        return getattr(self.master, item)

    def add_clone(self):
        raise NotImplementedError()

    def remove_clone(self, port):
        raise NotImplementedError()
