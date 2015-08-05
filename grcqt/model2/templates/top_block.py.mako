<%!
    def indent(level=0, first_line=True):
        def _indent(x):
            spaces = ' ' * (4 * level)
            indented = '\n'.join(spaces + line for line in x.split('\n'))
            return spaces + indented if first_line else indented.strip()
        return _indent
%>\
#!/usr/bin/env python2

# imports
% for import_ in get_imports(fg):
${ import_ }
% endfor\


class ${ fg.name }(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, ${ fg.name | repr })

        % for block in fg.blocks:
        self.${ block.name } = ${ block.name } = ${ get_block_make(block) | indent(2, False) }
        % endfor

        % for con in fg.connections:
        self.connect(${ con })
        % endfor\


if __name__ == '__main__':
    tb = ${ fg.name }()
    tb.start(${ fg.options.get('max_nouts', '') })
    tb.wait()
