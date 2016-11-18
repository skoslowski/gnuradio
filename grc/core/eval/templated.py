# Copyright 2016 Free Software Foundation, Inc.
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

from __future__ import absolute_import, print_function

from mako.template import Template#
from mako.exceptions import SyntaxException

from ..errors import TemplateError


class Templated(object):
    def __init__(self, name=None):
        self.name = name or 'templated_{}'.format(id(self))

    @property
    def name_raw(self):
        return '_' + self.name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        try:
            template = instance.__dict__[self.name]
        except KeyError:
            return instance.__dict__.get(self.name_raw, None)
        try:
            return template.render(**instance.namespace)
        except Exception as error:
            raise TemplateError(error)

    def __set__(self, instance, value):
        instance.__dict__[self.name_raw] = value
        value = str(value)
        if '${' in value or '%' in value:
            try:
                template = Template(value)
            except SyntaxException as error:
                raise TemplateError(value, *error.args)
            instance.__dict__[self.name] = template
