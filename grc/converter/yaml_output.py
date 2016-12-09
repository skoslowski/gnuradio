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

from __future__ import absolute_import

from collections import OrderedDict
import functools

import six
import yaml


class GRCDumper(yaml.Dumper):
    @classmethod
    def add(cls, data_type):
        def decorator(func):
            cls.add_representer(data_type, func)
            return func
        return decorator


@GRCDumper.add(OrderedDict)
def represent_ordered_mapping(representer, data):
    self = representer

    value = []
    node = yaml.MappingNode(u'tag:yaml.org,2002:map', value, flow_style=False)

    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node

    for item_key, item_value in six.iteritems(data):
        node_key = self.represent_data(item_key)
        node_value = self.represent_data(item_value)
        value.append((node_key, node_value))

    return node


class OrderedDictFlowing(OrderedDict):
    pass


@GRCDumper.add(OrderedDictFlowing)
def represent_ordered_mapping_flowing(representer, data):
    node = represent_ordered_mapping(representer, data)
    node.flow_style = True
    return node


@GRCDumper.add(yaml.nodes.ScalarNode)
def represent_node(representer, node):
    return node


class ListFlowing(list):
    pass


@GRCDumper.add(ListFlowing)
def represent_list_flowing(representer, data):
    node = representer.represent_list(data)
    node.flow_style = True
    return node


class Cheetah(str):
    pass


@GRCDumper.add(Cheetah)
def represent_cheetah_string(representer, data):
    return representer.represent_scalar(tag=u'!cheetah', value=data)


class MultiLineString(str):
    pass


@GRCDumper.add(MultiLineString)
def represent_ml_string(representer, data):
    node = representer.represent_str(data)
    node.style = '|'
    return node
