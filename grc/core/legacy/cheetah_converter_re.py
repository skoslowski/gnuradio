import re

from .yaml_output import Eval, Mako


class CheetahConversionException(Exception):
    pass

cheetah_substitution = re.compile(
    r'\$\*?'
    r'((?P<d1>\()|(?P<d2>\{)|(?P<d3>\[)|)'
    r'(?P<arg>[_a-zA-Z][_a-zA-Z0-9]*(?:\.[_a-zA-Z][_a-zA-Z0-9]*)?(?:\(\))?)'
    r'(?(d1)\)|(?(d2)\}|(?(d3)\]|)))'
    r'(?<!\. )'
)
cheetah_inline_if = re.compile(r'#if (?P<cond>.*) then (?P<then>.*) else (?P<else>.*) ?(#|$)')
cheetah_set = re.compile(r'^\w*#set (?P<set>.*)\w*($|#.*)')


def convert_cheetah_to_format_string(expr):
    """converts a basic Cheetah expr to python string formatting"""
    markers = ('__!!start!!__', '__!!end!!__')
    # replace and tag substitutions (only tag, because ${key} is valid Cheetah)
    expr = cheetah_substitution.sub('{}\g<arg>{}'.format(*markers), expr)
    # mask all curly braces (those left are not no substitutions)
    expr = expr.replace("{", "{{").replace("}", "}}")
    # finally, replace markers with curly braces
    expr = expr.replace(markers[0], "{").replace(markers[1], "}")

    if any(kw in expr for kw in ("#set", "#end", "$")):
        raise CheetahConversionException("Can't convert this expr", expr)

    return expr


def convert_cheetah_to_mako(expr):
    """converts a basic Cheetah expr to python string formatting"""
    output = []

    def convert_set_directive(match):
        arg = match.group('set')
        arg = cheetah_substitution.sub('\g<arg>', arg)
        return '<% {} %>'.format(arg)

    for line in expr.strip().splitlines():
        line = cheetah_set.sub(convert_set_directive, line)
        line = cheetah_substitution.sub('${ \g<arg> }', line)
        output.append(line)
    return Mako('\n'.join(output))


def convert_cheetah_to_python(expr):
    """converts a basic Cheetah expr to python string formatting"""
    expr = str(expr)
    if '$' not in expr:
        return expr
    expr = cheetah_substitution.sub('\g<arg>', expr)

    expr = cheetah_inline_if.sub(r'(\g<then> if \g<cond> else \g<else>)', expr)

    if any(kw in expr for kw in ("#set", "#end", "$")):
        raise CheetahConversionException("Can't convert this expr", expr)

    return Eval(expr)
