

import tempfile
import shutil
import os
import pytest

from zeus.core import (
    _default_crypto,
    encrypt,
    compute_decryption_factors,
    combine_decryption_factors,
    decrypt_with_decryptor,
    from_canonical,
    main,
)
from zeus.zeus_sk import mix_ciphers


def test_decryption():
    g = _default_crypto['generator']
    p = _default_crypto['modulus']
    q = _default_crypto['order']

    texts = [0, 1, 2, 3, 4]
    keys = [13, 14, 15, 16]
    publics = [pow(g, x, p) for x in keys]
    pk = 1
    for y in publics:
        pk = (pk * y) % p
    cts = []
    rands = []
    for t in texts:
        ct = encrypt(t, p, g, q, pk)
        cts.append((ct[0], ct[1]))
        rands.append(ct[2])

    all_factors = []
    for x in keys:
        factors = compute_decryption_factors(p, g, q, x, cts)
        all_factors.append(factors)

    master_factors = combine_decryption_factors(p, all_factors)
    pts = []
    for (alpha, beta), factor in zip(cts, master_factors):
        pts.append(decrypt_with_decryptor(p, g, q, beta, factor))
    assert pts == texts

    cfm = {'modulus': p,
           'generator': g,
           'order': q,
           'public': pk,
           'original_ciphers': cts,
           'mixed_ciphers': cts}

    mix1 = mix_ciphers(cfm)
    mix = mix_ciphers(mix1)
    cts = mix['mixed_ciphers']
    all_factors = []
    for x in keys:
        factors = compute_decryption_factors(p, g, q, x, cts)
        all_factors.append(factors)

    master_factors = combine_decryption_factors(p, all_factors)
    pts = []
    for (alpha, beta), factor in zip(cts, master_factors):
        pts.append(decrypt_with_decryptor(p, g, q, beta, factor))
    assert sorted(pts) == sorted(texts)


# Test both single-process and parallel version.
@pytest.mark.parametrize('processes', [0, 2])
def test_generate(processes):
    d = tempfile.mkdtemp(prefix='zeus')
    try:
        filename = os.path.join(d, 'election.json')
        main(['--generate', filename, '--parallel', str(processes)])
        # Parse the results back.
        with open(filename) as f:
            election = from_canonical(f)
    finally:
        shutil.rmtree(d)
