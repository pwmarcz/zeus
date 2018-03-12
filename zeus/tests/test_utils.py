from zeus.utils import decalize, undecalize


def test_decalize():
    import random
    alphabet = 'abcdefghkmnpqrstuvwxyzABCDEFGHKLMNPQRSTUVWXYZ23456789'

    N = 1000
    for i in xrange(N):
        s = ''
        for j in xrange(12):
            s += random.choice(alphabet)
        dec = decalize(s, sep='-', chunk=2)
        #print s, '-', dec
        undec = undecalize(dec)
        if undec != s:
            m = "%s %s %s %s" % (i, s, dec, undec)
            raise AssertionError("decalize-undecalize mismatch: %s" % m)

    if decalize("") != undecalize(""):
        raise AssertionError()

    if decalize(" ") != "00":
        raise AssertionError()

    if undecalize("00") != " ":
        raise AssertionError()

    if undecalize("95") != "\x7f":
        raise AssertionError()

    decalize_tests = ["\x1f", "\x80"]
    for t in decalize_tests:
        try:
            decalize(t)
        except ValueError as e:
            pass
        else:
            raise AssertionError("Decalize(%s) failed to fail" % t)

    undecalize_tests = ["9012-3", "42019609"]
    for t in undecalize_tests:
        try:
            undecalize(t)
        except ValueError as e:
            pass
        else:
            raise AssertionError("Undecalize(%s) failed to fail" % t)
