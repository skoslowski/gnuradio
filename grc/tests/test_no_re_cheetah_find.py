# -*- coding: utf-8 -*-
""""""

import string
import collections
import functools


delims = {'(': ')', '[': ']', '{': '}'}
identifier_start = '_' + string.ascii_letters + ''.join(delims.keys())


class Spec:
    start = ''
    end = ''
    nested_start = ''
    nested_end = ''


def cheetah_to_python(expr, names, spec=Spec):
    counts = collections.Counter()

    def all_delims_closed():
        for opener_, closer_ in delims.items():
            if counts[opener_] != counts[closer_]:
                return False
        return True

    out = []
    delim_to_find = False

    pos = 0
    char = ''
    while pos < len(expr):
        prev, char = char, expr[pos]
        counts.update(char)

        if char == '$':
            pass

        elif prev == '$':
            if char not in identifier_start:
                out.append('$' + char)

            elif not delim_to_find:
                try:
                    delim_to_find = delims[char]
                    pos += 1
                    continue
                except KeyError:
                    if char in identifier_start:
                        delim_to_find = ' '
                        out.append(char)

            else:
                for known_identifier in names:
                    if expr[pos:].startswith(known_identifier):
                        out.append(spec.nested_start)
                        out.append(known_identifier)
                        out.append(spec.nested_end)
                        pos += len(known_identifier)
                        continue

        elif char == delim_to_find and all_delims_closed():
            if delim_to_find == ' ':
                out.append(' ')

            delim_to_find = False
            counts.clear()

        else:
            out.append(char)

        pos += 1

    return ''.join(out)


c2p = functools.partial(cheetah_to_python, names=['abc'])


def test_simple():
    assert 'abc abc abc' == c2p('$abc $(abc) ${abc}')
    assert 'abc abc.abc abc' == c2p('$abc $abc.abc ${abc}')
    assert 'abc abc[''].abc() abc' == c2p('$abc $abc[''].abc() ${abc}')


def test_nested():
    assert 'abc(abc) abc + abc abc[abc]' == c2p('$abc($abc) $(abc + $abc) ${abc[$abc]}')


def test_nested():

    class MySpec(Spec):
        nested_start = '{'
        nested_end = '}'

    assert 'abc({abc})' == cheetah_to_python('$abc($abc)', ['abc'], MySpec)
