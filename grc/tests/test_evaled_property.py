import collections
from grc.core.Element import Evaluated, EvaluatedEnum, EvaluatedPInt


class A(object):
    def __init__(self, **kwargs):
        self.called = collections.defaultdict(int)
        self.namespace = kwargs
    @property
    def parent_block(self):
        return self

    def evaluate(self, expr):
        self.called['evaluate'] += 1
        return eval(expr, self.namespace)

    @Evaluated(int, 1)
    def foo(self):
        self.called['foo'] += 1
        return eval(self._foo)

    bar = Evaluated(float, 1.0, name='bar')

    test = EvaluatedEnum(['a', 'b'], 'a', name='test')

    lala = EvaluatedPInt()


def test_fixed_value():
    a = A()
    a.foo = 10

    assert getattr(a, '_foo') == 10
    assert a.foo == 10
    assert a.called['foo'] == 0
    delattr(a, 'foo')
    assert a.foo == 10
    assert a.called['foo'] == 0


def test_evaled():
    a = A()
    a.foo = '10 + 1'
    assert getattr(a, '_foo') == '10 + 1'
    assert a.foo == 11 and a.foo == 11
    assert a.called['foo'] == 1
    assert a.called['evaluate'] == 0
    delattr(a, 'foo')
    assert a.foo == 11 and a.foo == 11
    assert a.called['foo'] == 2


def test_evaled_with_default():
    a = A()
    a.bar = '10 + 1'
    assert getattr(a, '_bar') == '10 + 1'
    assert a.bar == 11.0 and type(a.bar) == float
    assert a.called['evaluate'] == 1


def test_evaled_int_with_default():
    a = A(ll=10)
    a.lala = 'll * 2'
    assert a.lala == 20
    a.namespace['ll'] = -10
    assert a.lala == 20
    del a.lala
    assert a.lala == 1


def test_evaled_enum_fixed_value():
    a = A()
    a.test = 'a'
    assert getattr(a, '_test') == 'a'
    assert a.test == 'a' and type(a.test) == str


def test_evaled_enum():
    a = A(bla=False)
    a.test = '"a" if bla else "b"'
    assert a.test == 'b'
    a.namespace['bla'] = True
    assert a.test == 'b'
    del a.test
    assert a.test == 'a'


def test_class_access():
    a = A()
    a.foo = 'meme'
    descriptor = getattr(a.__class__, 'foo')
    assert descriptor.name_raw == '_foo'
    assert getattr(a, descriptor.name_raw) == 'meme'
