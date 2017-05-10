from zeus.core import (
        ZeusError, pow, sha256, ALPHA, BETA,
        get_random_int, bit_iterator, get_random_permutation,
        Random, AsyncController, MIN_MIX_ROUNDS, _teller)


def reencrypt(modulus, generator, order, public, alpha, beta, secret=None):
    key = get_random_int(3, order) if secret is None else secret
    alpha = (alpha * pow(generator, key, modulus)) % modulus
    beta = (beta * pow(public, key, modulus)) % modulus
    if secret is None:
        return [alpha, beta, key]
    return [alpha, beta]


def compute_mix_challenge(cipher_mix):
    hasher = sha256()
    update = hasher.update

    update("%x" % cipher_mix['modulus'])
    update("%x" % cipher_mix['generator'])
    update("%x" % cipher_mix['order'])
    update("%x" % cipher_mix['public'])

    original_ciphers = cipher_mix['original_ciphers']
    for cipher in original_ciphers:
        update("%x" % cipher[ALPHA])
        update("%x" % cipher[BETA])

    mixed_ciphers = cipher_mix['mixed_ciphers']
    for cipher in mixed_ciphers:
        update("%x" % cipher[ALPHA])
        update("%x" % cipher[BETA])

    for ciphers in cipher_mix['cipher_collections']:
        for cipher in ciphers:
            update("%x" % cipher[ALPHA])
            update("%x" % cipher[BETA])

    challenge = hasher.hexdigest()
    return challenge


def shuffle_ciphers(modulus, generator, order, public, ciphers,
                    teller=None, report_thresh=128, async_channel=None):
    nr_ciphers = len(ciphers)
    mixed_offsets = get_random_permutation(nr_ciphers)
    mixed_ciphers = list([None]) * nr_ciphers
    mixed_randoms = list([None]) * nr_ciphers
    count = 0

    for i in xrange(nr_ciphers):
        alpha, beta = ciphers[i]
        alpha, beta, secret = reencrypt(modulus, generator, order, public,
                                        alpha, beta)
        mixed_randoms[i] = secret
        o = mixed_offsets[i]
        mixed_ciphers[o] = [alpha, beta]
        count += 1
        if count >= report_thresh:
            if teller:
                teller.advance(count)
            if async_channel:
                async_channel.send_shared(count, wait=1)
            count = 0

    if count:
        if teller:
            teller.advance(count)
        if async_channel:
            async_channel.send_shared(count, wait=1)
    return [mixed_ciphers, mixed_offsets, mixed_randoms]


def mix_ciphers(ciphers_for_mixing, nr_rounds=MIN_MIX_ROUNDS,
                teller=_teller, nr_parallel=0):
    p = ciphers_for_mixing['modulus']
    g = ciphers_for_mixing['generator']
    q = ciphers_for_mixing['order']
    y = ciphers_for_mixing['public']

    original_ciphers = ciphers_for_mixing['mixed_ciphers']
    nr_ciphers = len(original_ciphers)

    if nr_parallel > 0:
        Random.atfork()
        async = AsyncController(parallel=nr_parallel)
        async_shuffle_ciphers = async.make_async(shuffle_ciphers)

    teller.task('Mixing %d ciphers for %d rounds' % (nr_ciphers, nr_rounds))

    cipher_mix = {'modulus': p, 'generator': g, 'order': q, 'public': y}
    cipher_mix['original_ciphers'] = original_ciphers

    with teller.task('Producing final mixed ciphers', total=nr_ciphers):
        shuffled = shuffle_ciphers(p, g, q, y, original_ciphers, teller=teller)
        mixed_ciphers, mixed_offsets, mixed_randoms = shuffled
        cipher_mix['mixed_ciphers'] = mixed_ciphers

    total = nr_ciphers * nr_rounds
    with teller.task('Producing ciphers for proof', total=total):
        if nr_parallel > 0:
            channels = [async_shuffle_ciphers(p, g, q, y, original_ciphers,
                                              teller=None)
                        for _ in xrange(nr_rounds)]

            count = 0
            while count < total:
                nr = async.receive_shared()
                teller.advance(nr)
                count += nr

            collections = [channel.receive(wait=1) for channel in channels]
            async.shutdown()
        else:
            collections = [shuffle_ciphers(p, g, q, y,
                                           original_ciphers, teller=teller)
                           for _ in xrange(nr_rounds)]

        unzipped = [list(x) for x in zip(*collections)]
        cipher_collections, offset_collections, random_collections = unzipped
        cipher_mix['cipher_collections'] = cipher_collections
        cipher_mix['random_collections'] = random_collections
        cipher_mix['offset_collections'] = offset_collections

    with teller.task('Producing cryptographic hash challenge'):
        challenge = compute_mix_challenge(cipher_mix)
        cipher_mix['challenge'] = challenge

    bits = bit_iterator(int(challenge, 16))

    with teller.task('Answering according to challenge', total=nr_rounds):
        for i, bit in zip(xrange(nr_rounds), bits):
            ciphers = cipher_collections[i]
            offsets = offset_collections[i]
            randoms = random_collections[i]

            if bit == 0:
                # Nothing to do, we just publish our offsets and randoms
                pass
            elif bit == 1:
                # The image is given. We now have to prove we know
                # both this image's and mixed_ciphers' offsets/randoms
                # by providing new offsets/randoms so one can reencode
                # this image to end up with mixed_ciphers.
                # original_ciphers -> image
                # original_ciphers -> mixed_ciphers
                # Provide image -> mixed_ciphers
                new_offsets = list([None]) * nr_ciphers
                new_randoms = list([None]) * nr_ciphers

                for j in xrange(nr_ciphers):
                    cipher_random = randoms[j]
                    cipher_offset = offsets[j]
                    mixed_random = mixed_randoms[j]
                    mixed_offset = mixed_offsets[j]

                    new_offsets[cipher_offset] = mixed_offset
                    new_random = (mixed_random - cipher_random) % q
                    new_randoms[cipher_offset] = new_random

                offset_collections[i] = new_offsets
                random_collections[i] = new_randoms
                del ciphers, offsets, randoms
            else:
                m = "This should be impossible. Something is broken."
                raise AssertionError(m)

            teller.advance()
    teller.finish('Mixing')

    return cipher_mix


def verify_mix_round(p, g, q, y, i, bit, original_ciphers, mixed_ciphers,
                     ciphers, randoms, offsets,
                     teller=None, report_thresh=128, async_channel=None):
    nr_ciphers = len(original_ciphers)
    count = 0
    if bit == 0:
        for j in xrange(nr_ciphers):
            original_cipher = original_ciphers[j]
            a = original_cipher[ALPHA]
            b = original_cipher[BETA]
            r = randoms[j]
            new_a, new_b = reencrypt(p, g, q, y, a, b, r)
            o = offsets[j]
            cipher = ciphers[o]
            if new_a != cipher[ALPHA] or new_b != cipher[BETA]:
                m = ('MIXING VERIFICATION FAILED AT '
                     'ROUND %d CIPHER %d bit 0' % (i, j))
                raise AssertionError(m)
            count += 1
            if count >= report_thresh:
                if async_channel:
                    async_channel.send_shared(count)
                if teller:
                    teller.advance(count)
                count = 0
    elif bit == 1:
        for j in xrange(nr_ciphers):
            cipher = ciphers[j]
            a = cipher[ALPHA]
            b = cipher[BETA]
            r = randoms[j]
            new_a, new_b = reencrypt(p, g, q, y, a, b, r)
            o = offsets[j]
            mixed_cipher = mixed_ciphers[o]
            if new_a != mixed_cipher[ALPHA] or new_b != mixed_cipher[BETA]:
                m = ('MIXING VERIFICATION FAILED AT '
                     'ROUND %d CIPHER %d bit 1' % (i, j))
                raise AssertionError(m)
            count += 1
            if count >= report_thresh:
                if async_channel:
                    async_channel.send_shared(count)
                if teller:
                    teller.advance(count)
                count = 0
    else:
        m = "This should be impossible. Something is broken."
        raise AssertionError(m)

    if count:
        if async_channel:
            async_channel.send_shared(count)
        if teller:
            teller.advance(count)


def verify_cipher_mix(cipher_mix, teller=_teller, nr_parallel=0):
    try:
        p = cipher_mix['modulus']
        g = cipher_mix['generator']
        q = cipher_mix['order']
        y = cipher_mix['public']

        original_ciphers = cipher_mix['original_ciphers']
        mixed_ciphers = cipher_mix['mixed_ciphers']
        challenge = cipher_mix['challenge']
        cipher_collections = cipher_mix['cipher_collections']
        offset_collections = cipher_mix['offset_collections']
        random_collections = cipher_mix['random_collections']
    except KeyError, e:
        m = "Invalid cipher mix format"
        raise ZeusError(m, e)

    if compute_mix_challenge(cipher_mix) != challenge:
        m = "Invalid challenge"
        raise ZeusError(m)

    nr_ciphers = len(original_ciphers)
    nr_rounds = len(cipher_collections)
    teller.task('Verifying mixing of %d ciphers for %d rounds'
                 % (nr_ciphers, nr_rounds))

    if (len(offset_collections) != nr_rounds or
        len(random_collections) != nr_rounds):
        m = "Invalid cipher mix format: collections not of the same size!"
        raise ZeusError(m)

    #if not validate_cryptosystem(p, g, q, teller):
    #    m = "Invalid cryptosystem"
    #    raise AssertionError(m)

    if nr_parallel > 0:
        async = AsyncController(parallel=nr_parallel)
        async_verify_mix_round = async.make_async(verify_mix_round)

    total = nr_rounds * nr_ciphers
    with teller.task('Verifying ciphers', total=total):
        channels = []
        append = channels.append
        for i, bit in zip(xrange(nr_rounds), bit_iterator(int(challenge, 16))):
            ciphers = cipher_collections[i]
            randoms = random_collections[i]
            offsets = offset_collections[i]
            if nr_parallel <= 0:
                verify_mix_round(p, g, q, y,
                                 i, bit, original_ciphers,
                                 mixed_ciphers, ciphers,
                                 randoms, offsets,
                                 teller=teller)
            else:
                append(async_verify_mix_round(p, g, q, y, i, bit,
                                              original_ciphers,
                                              mixed_ciphers,
                                              ciphers, randoms, offsets,
                                              teller=None))
        if nr_parallel > 0:
            count = 0
            while count < total:
                nr = async.receive_shared(wait=1)
                teller.advance(nr)
                count += nr

            for channel in channels:
                channel.receive(wait=1)

            async.shutdown()

    teller.finish('Verifying mixing')
    return 1
