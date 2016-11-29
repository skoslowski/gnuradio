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

from mako.template import Template
from mako.exceptions import SyntaxException

from .errors import TemplateError


class MakoTemplates(dict):

    _template_cache = {}

    def __init__(self, block, *args, **kwargs):
        self.block = block
        dict.__init__(self, *args, **kwargs)

    def _get_template(self, text):
        try:
            return self._template_cache[text]
        except KeyError:
            pass

        try:
            template = Template(text)
        except SyntaxException as error:
            raise TemplateError(text, *error.args)

        self._template_cache[text] = template
        return template

    def render(self, item):
        text = self[item] or ''
        if isinstance(text, list):
            template = [self._get_template(t) for t in text]
        else:
            template = self._get_template(text)
        try:
            if isinstance(template, list):
                return [t.render(**self.block.namespace) for t in template]
            else:
                return template.render(**self.block.namespace)
        except Exception as error:
            raise TemplateError(error, template)
