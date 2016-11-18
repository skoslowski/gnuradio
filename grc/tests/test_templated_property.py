import collections

import pytest

from grc.core.eval import Templated
from grc.core.errors import TemplateError


class A(object):
    def __init__(self, **kwargs):
        self.called = collections.defaultdict(int)
        self.errors = []
        self.namespace = kwargs

    def add_error_message(self, msg):
        self.errors.append(msg)

    @property
    def parent_block(self):
        return self

    foo = Templated(name='foo')


def test_fixed_value():
    a = A()
    a.foo = '10'
    assert hasattr(a, '_foo')
    assert 'foo' not in a.__dict__


def test_no_str_fixed_value():
    a = A()
    a.foo = 10
    assert hasattr(a, '_foo')
    assert 'foo' not in a.__dict__
    assert getattr(a, '_foo') == 10


def test_mako_value():
    a = A(c=10)
    a.foo = '${ 1 + 2 * c }'
    assert a.foo == '21'


def test_mako_syntax_error():
    a = A()
    template = '${ 1 + }'
    with pytest.raises(TemplateError) as excinfo:
        a.foo = template
    assert excinfo.value[0] == template


def test_mako_render_error():
    a = A()
    template = '${ 1 + a }'  # a is missing
    a.foo = template
    with pytest.raises(TemplateError) as excinfo:
        a.foo
    assert isinstance(excinfo.value[0], TypeError)
