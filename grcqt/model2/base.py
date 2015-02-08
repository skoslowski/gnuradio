# Copyright 2014 Free Software Foundation, Inc.
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

from __future__ import absolute_import, division, print_function
import weakref
import collections
import contextlib

from . import exceptions


class lazyproperty(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value


class Element(object):

    def __init__(self):
        super(Element, self).__init__()
        self.children = []
        self.collected_errors = []

    def __str__(self):
        """Most elements have a label (blocks, ports, params, ...)"""
        return getattr(self, 'label', self.__class__.__name__)

    ###########################################################################

    def add_child(self, child):
        self.children.append(child)
        try:
            child.parent = self
        except AttributeError:
            pass

    @property
    def parent(self):
        return vars(self).get('parent', lambda: None)()

    @parent.setter
    def parent(self, value):
        vars(self)['parent'] = weakref.ref(value)

    def get_parent_by_class(self, cls):
        try:
            return self.parent if isinstance(self.parent, cls) else \
                self.parent.get_parent_by_class(cls)
        except AttributeError:
            return None

    @lazyproperty
    def parent_block(self):
        """Get the first block object in the ancestry

         Returns:
            a block object or None
        """
        from . blocks import BaseBlock
        return self.get_parent_by_class(BaseBlock)

    @lazyproperty
    def parent_flowgraph(self):
        """Get the first flow-graph object in the ancestry

         Returns:
            a flow-graph object or None
        """
        from . flowgraph import FlowGraph
        return self.get_parent_by_class(FlowGraph)

    @lazyproperty
    def platform(self):
        """Get the platform object from the ancestry

         Returns:
            a platform object or None
        """
        from . platform import Platform
        return self.get_parent_by_class(Platform)

    def reset_lazyproperties(self):
        """Reset all lazy properties"""
        # todo: use case?
        for name, obj in vars(Element):
            if isinstance(obj, lazyproperty):
                delattr(self, name)

    ###########################################################################

    def validate(self):
        """Validate object and all child object in this tree

        Validation shall only check the validity of the flow-graph, not change
        any values
        """
        for child in self.children:
            child.validate()

    def add_error(self, err_or_msg):
        """Format and add an error message for this element"""
        if isinstance(err_or_msg, str):
            err_or_msg = Exception(err_or_msg.format(self=self))
        if not isinstance(err_or_msg, Exception):
            err_or_msg = Exception(err_or_msg)
        self.collected_errors.append(err_or_msg)

    @property
    def is_valid(self):
        """Check if this element is valid"""
        return (not self.collected_errors and
                all(child.is_valid for child in self.children))

    def iter_error_messages(self, recursive=True):
        for err in self.collected_errors:
            yield self, err
        if recursive:
            for child in self.children:
                for err in child.iter_error_messages():
                    yield err

    def clear_error_messages(self, recursive=True):
        """Clear error messages in this and all child objects"""
        del self.collected_errors[:]
        if recursive:
            for child in self.children:
                child.clear_error_messages()


class ElementWithUpdate(Element):
    """Adds installable update callbacks for specific attributes"""

    def __init__(self):
        super(ElementWithUpdate, self).__init__()
        self.update_actions = {}

    def update(self):
        """Perform an update of this object using a set of callbacks"""
        params = self.parent_block.namespace
        for target, callback_or_param_name in self.update_actions.iteritems():
            try:
                if callable(callback_or_param_name):
                    value = callback_or_param_name(**params)
                else:
                    value = params[callback_or_param_name]
                setattr(self, target, value)
            except Exception as e:  # Never throw during update
                self.add_error("Failed to update '{}.{}': {}".format(
                    self, target, e.args[0]
                ))

    def on_update(self, **kwargs):
        """This installs a number of callbacks in the objects update function

        The object must a child of a Block. The key of each argument must be a
        valid attribute of the object. The values are callables with a single
        argument. On update a dict of parameter keys and evaluated value is
        passed.

        As a shorthand a parameter key (string) can be passed instead of a
        callable. The parameter value is used to update the attribute.
        """
        invalid_attr_names = []
        for attr_name, callback in kwargs.iteritems():
            if hasattr(self, attr_name):  # todo: exclude methods
                self.update_actions[attr_name] = callback
            else:
                invalid_attr_names.append(attr_name)
        if invalid_attr_names:
            raise exceptions.BlockSetupException(
                "No attribute(s) founds for " + str(invalid_attr_names))


class Namespace(collections.OrderedDict):
    """A dict class that auto-calls variables for missing names"""

    def __init__(self, items):
        super(Namespace, self).__init__()
        self.elements = items
        self.auto_resolved_keys = []
        self._auto_resolve = True
        self._getitem_recursion_keys = []

    @contextlib.contextmanager
    def auto_resolve_off(self):
        try:
            self._auto_resolve = False
            yield
        finally:
            self._auto_resolve = True

    def _set_value_from_element(self, key):
        if isinstance(self.elements, list):
            for element in self.elements:
                if element.uid == key:
                    break
            else:
                return
        else:
            try:
                element = self.elements[key]
            except KeyError:
                return
        element.update()
        self.auto_resolved_keys.append(key)
        if element.is_valid:
            self[key] = element.evaluated

    def __getitem__(self, key):
        if key in self._getitem_recursion_keys:
            raise NameError("label {!r} is not defined".format(key))
        if self._auto_resolve and key not in self:
            self._getitem_recursion_keys.append(key)
            self._set_value_from_element(key)
            self._getitem_recursion_keys.remove(key)
        return super(Namespace, self).__getitem__(key)

    def clear(self):
        super(Namespace, self).clear()
        del self.auto_resolved_keys[:]
        del self._getitem_recursion_keys[:]
