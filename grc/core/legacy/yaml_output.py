from collections import OrderedDict
import functools

import six
import yaml


class Eval(unicode):
    """String subtype explicitly enable evaluation of the provided expression"""
    tag = u'!eval'


class Mako(unicode):
    """String subtype explicitly enable evaluation of the provided expression"""
    tag = u'!mako'


class Chettah(unicode):
    """String subtype explicitly enable evaluation of the provided expression"""
    tag = u'!cheetah'


class OrderedDictFlowing(OrderedDict):
    pass


def yaml_constructor(data_type):
    def decorator(func):
        yaml.add_constructor(data_type.tag, func)
        return func
    return decorator


def yaml_representer(data_type):
    def decorator(func):
        yaml.add_representer(data_type, func)
        return func
    return decorator


@yaml_constructor(Eval)
def construct_code_string(loader, node):
    return Eval(loader.construct_scalar(node))


@yaml_representer(Eval)
def represent_code_string(representer, data):
    node = representer.represent_scalar(tag=Eval.tag, value=data)
    if "'" in data and '"' not in data:
        node.style = '"'
    return node


@yaml_representer(Mako)
def represent_mako_string(representer, data):
    return representer.represent_scalar(tag=Mako.tag, value=data)


@yaml_representer(OrderedDict)
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


@yaml_representer(OrderedDictFlowing)
def represent_ordered_mapping_flowing(representer, data):
    node = represent_ordered_mapping(representer, data)
    node.flow_style = True
    return node


@yaml_representer(yaml.nodes.ScalarNode)
def represent_node(representer, node):
    return node

scalar_node = functools.partial(yaml.ScalarNode, u'tag:yaml.org,2002:str')
