from collections import OrderedDict
import functools

import six
import yaml

from ..utils.yaml_loader import Eval, Mako, Cheetah


class GRCDumper(yaml.Dumper):
    @classmethod
    def add(cls, data_type):
        def decorator(func):
            cls.add_representer(data_type, func)
            return func
        return decorator


@GRCDumper.add(Eval)
def represent_code_string(representer, data):
    node = representer.represent_scalar(tag=Eval.tag, value=data)
    if "'" in data and '"' not in data:
        node.style = '"'
    return node


@GRCDumper.add(Mako)
def represent_mako_string(representer, data):
    return representer.represent_scalar(tag=Mako.tag, value=data)


@GRCDumper.add(Cheetah)
def represent_cheetah_string(representer, data):
    return representer.represent_scalar(tag=Cheetah.tag, value=data)


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


scalar_node = functools.partial(yaml.ScalarNode, u'tag:yaml.org,2002:str')
