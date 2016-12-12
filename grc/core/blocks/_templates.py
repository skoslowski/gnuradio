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
"""
This dict class holds a (shared) cache of compiled mako templates.
These

"""
from __future__ import absolute_import, print_function

from mako.template import Template
from mako.exceptions import SyntaxException

from ..errors import TemplateError


class MakoTemplates(dict):

    _template_cache = {}

    def __init__(self, block, *args, **kwargs):
        self.block = block
        dict.__init__(self, *args, **kwargs)

    @classmethod
    def compile(cls, text):
        text = str(text)
        try:
            template = Template(text)
        except SyntaxException as error:
            raise TemplateError(text, *error.args)

        cls._template_cache[text] = template
        return template

    def _get_template(self, text):
        try:
            return self._template_cache[str(text)]
        except KeyError:
            return self.compile(text)

    def render(self, item):
        text = self[item] or ''

        try:
            if isinstance(text, list):
                templates = (self._get_template(t) for t in text)
                return [template.render(**self.block.namespace_templates)
                        for template in templates]
            else:
                template = self._get_template(text)
                return template.render(**self.block.namespace_templates)
        except Exception as error:
            raise TemplateError(error, text)
