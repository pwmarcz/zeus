import pytest
from zeus.utils import decalize, undecalize

@pytest.mark.parametrize(('s', 'dec'), [
    ('', ''),
    (' ', '00'),
    ('\x7f', '95'),
])
def test_simple(s, dec):
    assert decalize(s) == dec
    assert undecalize(dec) == s


def random_strings(n):
    import random
    random.seed(42)
    alphabet = 'abcdefghkmnpqrstuvwxyzABCDEFGHKLMNPQRSTUVWXYZ23456789'
    return [
        ''.join(random.choice(alphabet) for j in xrange(12))
        for i in xrange(n)
    ]


@pytest.mark.parametrize('s', random_strings(10))
def test_decalize_random(s):
    dec = decalize(s, sep='-', chunk=2)
    assert undecalize(dec) == s


@pytest.mark.parametrize('s', ['\x1f', '\x80'])
def test_decalize_fail(s):
    with pytest.raises(ValueError):
        decalize(s)


@pytest.mark.parametrize('s', ["9012-3", "42019609"])
def test_undecalize_fail(s):
    with pytest.raises(ValueError):
        undecalize(s)
