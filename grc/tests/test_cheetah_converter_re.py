
import textwrap

from grc.core.legacy.cheetah_converter_re import (
    convert_cheetah_to_format_string,
    convert_cheetah_to_mako as to_mako
)


def test_cheetah_to_mako_simple():
    assert '${ te.st } ${ te_st } ${ test() }' == to_mako('${te.st} $[te_st] $test()')


def test_cheetah_to_mako_set():
    cheetah = textwrap.dedent("""
        #set $abs = 123
        $[working]
    """).strip()
    mako = textwrap.dedent("""
        <% abs = 123 %>
        ${ working }
    """).strip()

    assert mako == to_mako(cheetah)


# def test_cheetah_to_mako_inline_if():
#     cheetah = '#if $abc = 123 then "helo" else "eloh" #'
#     mako = ''
#     assert mako == to_mako(cheetah)


def test_convert_cheetah_template():
    make = convert_cheetah_to_format_string("{test$a} $(abc123_a3) ${a}a $[a]lk $(b.cd)")
    assert make == "{{test{a}}} {abc123_a3} {a}a {a}lk {b.cd}"


def test_convert_cheetah_template2():
    make = convert_cheetah_to_format_string("[$abc] $test]")
    assert make == "[{abc}] {test}]"
