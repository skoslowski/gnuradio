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

from collections import OrderedDict

from jinja2 import Environment, FileSystemLoader


import model2

fg = model2.FlowGraph()


class MyBlock(model2.Block):

    import_template = """
        import bla
        import foo
    """

    make_template = """\
        bla.foo()"""

    def setup(self, **kwargs):
        pass

b = MyBlock()
b.make_template = ''
b.import_template = 'import {{ b1 }}'
p = model2.Param("b1", "b1", vtype='raw')
p.value = "block_1"
b.add_param(p)
fg.add_block(b)

fg.add_block(MyBlock())

b = MyBlock()
b.make_template = ''
p = model2.Param("t1", "test label", vtype='raw', default='block_0')
b.add_param(p)
p = model2.Param("t2", "test label", vtype=int)
b.add_param(p)
fg.add_block(b)

fg.add_block(MyBlock())

fg.update()
for err in fg.iter_errors():
    print(err)

assert fg.is_valid

env = Environment(
    loader=FileSystemLoader('./templates'),
    extensions=['jinja2.ext.with_']
)


ignored_params = ('name', 'alias', 'affinity', 'minoutbuf', 'maxoutbuf')


def render_user_template(template, block):
    # clean-out extra indents
    template = template.strip('\n')
    leading_whitespace = len(template) - len(template.lstrip())
    template = '\n'.join(line[leading_whitespace:] for line in template.split('\n'))
    # prepare param namespace
    namespace = OrderedDict(
        (name, param.value)
        for name, param in block.params.items() if name not in ignored_params
    )
    # render template
    return env.from_string(template).render(namespace)


def get_block_make(block):
    if block.make_template:
        make = render_user_template(block.make_template, block)

    else:
        make = "{}({})".format(block.typename, ", ".join(
            "{}={}".format(name, param.value)
            for name, param in block.params.items() if name not in ignored_params
        ))

    return make


def get_imports(fg):
    imports = set(fg.options.get('imports', []))
    for block in fg.blocks:
        import_ = render_user_template(block.import_template, block)
        imports.add(import_)
    return imports


top_block_template = env.get_template('top_block.py.jinja2')


print(top_block_template.render(
    fg=fg,
    get_block_make=get_block_make,
    get_imports=get_imports,
    render_block_template_from_string=render_user_template,
))

