# -*- coding: utf-8 -*-

import yaml
import pprint


class Code(unicode):
    """String subtype explicitly enable evaluation of the provided expression"""

yaml.add_constructor(u'!code', lambda loader, node:
    Code(loader.construct_scalar(node)))


block_data = """

label: Add                            # former <name>
name:  blocks_add_xx                  # former <key>

params:                               # a sequence of mappings

    - name:    type                   # former <key>
      label:   IO Type
      type:    enum
      options: &type_emum             # tag this for reuse
        - {value: complex, label: Complex}
        - {value: float,   label: Float}
        - int   # if no label is needed
        # no <opt> supported. I'd rather shift that to make (see below)

    - name:  other
      label: Other Parameter
      type:  !code type               # explicit declaration of model code
                                      # all other values are considered static.

    - name:  num_inputs               # these define the 'block namespace'
      label: Num Inputs
      type:  int
      default: 2

    - name:  vlen
      label: Vec Length
      type:  int
      default: 1
      hide:  !code ('all' if num_inputs > 5 else 'part')

      # if a string starts with a quote, parsing fails. Either use parenthesis
      # or switch to block notation (see below)

    - name:    other_type                # former <key>
      label:   IO Type2
      type:    enum
      options: *type_emum                # use prev defined enum

checks:
    - !code num_inputs > 1
    - !code len > 0

ports:
    - type:      stream_sink              # new port type: message/stream _ sink/source
      label:     in
      duplicate: num_inputs               # former <nports>
      dtype:     !code type               # former <type> now, the data type
      vlen:      !code vlen

    - {label: out, type: stream_source, dtype: !code type, vlen: !code vlen}

    - type:     message_source
      label:    test
      key:      mytest
      optional: True

import: |
    from gnuradio import blocks            # multi-line
    import this

make: |
    blocks.add_v${ {'complex':'cc', 'float':'ff' }[type] })(${ vlen })    # mako here

# YAML implicit type parsing is somewhat fragile when you put model/mako code
# in there. I found using the block notation (notice |) eliminates this problem
# and also looks cleaner.

callbacks:
    - set_something(${ the new value})      # again mako
    - set_other(1 + 2* ${ vlen })

documentation: |
    Beautiful is better than ugly.
    Explicit is better than implicit.
    Simple is better than complex.
    ...

"""

parsed_block_data = yaml.load(block_data)
pprint.pprint(parsed_block_data)
assert isinstance(parsed_block_data['ports'][0]['dtype'], Code)
