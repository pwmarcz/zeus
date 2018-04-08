#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os
import ssl

from zeus.core import (c2048, get_random_selection,
                       gamma_encode, gamma_decode, gamma_encoding_max,
                       to_relative_answers, to_absolute_answers,
                       to_canonical, from_canonical,
                       encrypt, prove_encryption,
                       decrypt_with_randomness,
                       compute_decryption_factors,
                       verify_vote_signature,
                       parties_from_candidates,
                       FormatError)

from six.moves.http_client import HTTPConnection, HTTPSConnection
from six.moves.urllib.parse import urlparse, parse_qsl
from six.moves.urllib.parse import urlencode
from os.path import exists
from json import loads, dumps, load, dump
from six.moves.queue import Queue, Empty
from threading import Thread
from random import choice, shuffle, randint
from base64 import b64encode

p, g, q, x, y = c2048()


def get_http_connection(url):
    parsed = urlparse(url)
    kwargs = {}
    if parsed.scheme == 'https':
        default_port = '443'
        Conn = HTTPSConnection
        kwargs['context'] = ssl._create_unverified_context()
    else:
        default_port = '80'
        Conn = HTTPConnection
    host, sep, port = parsed.netloc.partition(':')
    if not port:
        port = default_port
    netloc = host + ':' + port
    conn = Conn(netloc, **kwargs)
    conn.path = parsed.path
    return conn


def generate_voter_file(nr, domain='zeus.minedu.gov.gr'):
    return '\n'.join(('%d, voter-%d@%s, Ψηφοφόρος, %d' % (i, i, domain, i))
                     for i in range(nr))


def generate_vote(p, g, q, y, choices):
    if isinstance(choices, int):
        nr_candidates = choices
        selection = get_random_selection(nr_candidates, full=0)
    else:
        nr_candidates = (max(choices) if choices else 0) + 1
        selection = to_relative_answers(choices, nr_candidates)
    encoded = gamma_encode(selection, nr_candidates)
    ct = encrypt(encoded, p, g, q, y)
    alpha, beta, rand = ct
    proof = prove_encryption(p, g, q, alpha, beta, rand)
    commitment, challenge, response = proof
    answer = {}
    answer['encryption_proof'] = (commitment, challenge, response)
    answer['choices'] = [{'alpha': alpha, 'beta': beta}]
    encrypted_vote = {}
    encrypted_vote['answers'] = [answer]
    encrypted_vote['election_uuid'] = ''
    encrypted_vote['election_hash'] = ''
    return encrypted_vote, encoded, rand


def main_verify(sigfile, randomness=None, plaintext=None):
    with open(sigfile) as f:
        signature = f.read()

    vote_info = verify_vote_signature(signature)
    signed_vote, crypto, trustees, candidates, comments = vote_info

    eb = signed_vote['encrypted_ballot']
    public = eb['public']
    modulus, generator, order = crypto
    beta = eb['beta']
    print('VERIFIED: Authentic Signature')
    if randomness is None:
        return

    nr_candidates = len(candidates)
    encoded = decrypt_with_randomness(modulus, generator, order,
                                      public, beta, randomness)
    if plaintext is not None:
        if plaintext != encoded:
            print('FAILED: Plaintext Mismatch')

        ct = encrypt(plaintext, modulus, generator, order, randomness)
        _alpha, _beta, _randomness = ct
        alpha = eb['alpha']
        if (alpha, beta) != (_alpha, _beta):
            print('FAILED: Invalid Encryption')

    max_encoded = gamma_encoding_max(nr_candidates) + 1
    print("plaintext:       %d" % encoded)
    print("max plaintext:   %d" % max_encoded)
    if encoded > max_encoded:
        print("FAILED: Invalid Vote. Cannot decode.")
        return

    selection = gamma_decode(encoded, nr_candidates)
    choices = to_absolute_answers(selection, nr_candidates)
    print("")
    for i, o in enumerate(choices):
        print("%d: [%d] %s" % (i, o, candidates[o]))
    print("")


def get_poll_info(url):
    conn = get_http_connection(url)
    path = conn.path
    conn.request('GET', path)
    response = conn.getresponse()
    response.read()
    cookie = response.getheader('Set-Cookie')
    if not cookie:
        raise RuntimeError("Cannot get cookie")
    cookie = cookie.split(';')[0]
    headers = {'Cookie': cookie}
    poll_intro = response.getheader('location')
    poll_intro = '/' + poll_intro.split("/", 3)[3]

    conn.request('GET', poll_intro, headers=headers)
    response = conn.getresponse()
    html = response.read()

    try:
        parsed = urlparse(html.split('<a id="booth-link"')[1].split('href="')[1].split('"')[0])
    except:
        print(html)
        raise
    poll_url = dict(parse_qsl(parsed.query))['continue_url']
    parsed = urlparse(poll_url)
    booth_path = parsed.path
    poll_info = dict(parse_qsl(parsed.query))
    poll_json_path = urlparse(poll_info['poll_json_url']).path
    conn.request('GET', poll_json_path, headers=headers)
    response = conn.getresponse()
    poll_info['poll_data'] = loads(response.read())
    return conn, headers, poll_info


def do_cast_vote(conn, cast_path, token, headers, vote):
    body = urlencode({'encrypted_vote': dumps(vote), 'csrfmiddlewaretoken': token})
    conn.request('POST', cast_path, headers=headers, body=body)
    response = conn.getresponse()
    body = response.read()
    if response.status != 200:
        print(response.status)
    conn.close()


def cast_vote(voter_url, choices=None):
    conn, headers, poll_info = get_poll_info(voter_url)
    csrf_token = poll_info['token']
    headers['Cookie'] += "; csrftoken=%s" % csrf_token
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    headers['Referer'] = voter_url

    voter_path = conn.path
    poll_data = poll_info['poll_data']
    pk = poll_data['public_key']
    p = int(pk['p'])
    g = int(pk['g'])
    q = int(pk['q'])
    y = int(pk['y'])
    candidates = poll_data['questions'][0]['answers']
    cast_path = poll_data['cast_url']

    parties = None
    try:
        parties, nr_groups = parties_from_candidates(candidates)
    except FormatError as e:
        pass

    if parties:
        if randint(0, 19) == 0:
            choices = []
        else:
            party_choice = choice(list(parties.keys()))
            party = parties[party_choice]
            party_candidates = [k for k in list(party.keys()) if isinstance(k, int)]
            min_choices = party['opt_min_choices']
            max_choices = party['opt_max_choices']
            shuffle(party_candidates)
            nr_choices = randint(min_choices, max_choices)
            choices = party_candidates[:nr_choices]
            choices.sort()
        vote, encoded, rand = generate_vote(p, g, q, y, choices)
        #for c in choices:
        #    print "Voting for", c, party[c]
        #ballot = gamma_decode_to_party_ballot(encoded, candidates,
        #                                      parties, nr_groups)
        #print "valid", ballot['valid'], ballot['invalid_reason']
        #print " "
    else:
        choices = choices if choices is not None else len(candidates)
        vote, encoded, rand = generate_vote(p, g, q, y, choices)

    do_cast_vote(conn, cast_path, csrf_token, headers, vote)
    return encoded, rand


def main_generate(nr, domain, voters_file):
    if exists(voters_file):
        m = "%s: file exists, will not overwrite" % (voters_file,)
        raise ValueError(m)

    with open(voters_file, "w") as f:
        f.write(generate_voter_file(nr, domain=domain).encode('utf-8'))


def main_random_cast_thread(inqueue, outqueue):
    while 1:
        try:
            o = inqueue.get_nowait()
            if not o:
                break
        except Empty as e:
            break
        i, total, voter_url = o
        print("%d/%d" % (i+1, total))
        encoded, rand = cast_vote(voter_url)
        outqueue.put(encoded)


def main_random_cast(voter_url_file, plaintexts_file, nr_threads=2):
    if exists(plaintexts_file):
        m = "%s: file exists, will not overwrite" % (plaintexts_file,)
        raise ValueError(m)
    f = open(plaintexts_file, "w")

    with open(voter_url_file) as f:
        voter_urls = f.read().splitlines()
    total = len(voter_urls)
    inqueue = Queue(maxsize=total)
    outqueue = Queue(maxsize=total)
    for i, voter_url in enumerate(voter_urls):
        inqueue.put((i, total, voter_url))

    #main_random_cast_thread(queue)
    threads = [Thread(target=main_random_cast_thread, args=(inqueue, outqueue))
               for _ in range(nr_threads)]

    for t in threads:
        t.daemon = True
        t.start()

    plaintexts = [outqueue.get() for _ in range(total)]
    f.write(repr(plaintexts))
    f.close()

    for t in threads:
        t.join()


def main_show(url):
    raise NotImplemented()
    '''
    conn, cast_path, token, headers, answers, p, g, q, y = get_election(url)
    for i, c in enumerate(answers):
        if isinstance(c, unicode):
            c = c.encode('utf-8')
        print "%d: %s" % (i, c)
    '''


def main_vote(url, choice_str):
    choices = [int(x) for x in choice_str.split(',')]
    encoded, rand = cast_vote(url, choices)
    print("encoded selection:", encoded)
    print("encryption randomness:", rand)


def do_download_mix(url, savefile):
    if exists(savefile):
        m = "file '%s' already exists, will not overwrite" % (savefile,)
        raise ValueError(m)

    conn = get_http_connection(url)
    conn.request('GET', conn.path)
    response = conn.getresponse()
    save_data = response.read()

    if "polls" not in url:
        polls = loads(save_data)
        for i, url in enumerate(polls):
            do_download_mix(url, "{}.{}".format(savefile, i))
        return

    with open(savefile, "w") as f:
        f.write(save_data)

    return save_data


def get_login(url):
    conn = get_http_connection(url)
    parsed = urlparse(url)

    _, _, election, _, _, trustee, password = parsed.path.split("/")
    auth = b64encode("%s:%s:%s" % (election, trustee, password))
    headers = {
        'Authorization': 'Basic %s' % auth
    }
    base_url = "/elections/%s/trustee" % (election,)
    return conn, headers, base_url


def get_election_info(url):
    conn, headers, url = get_login(url)
    conn.request('GET', url + '/json', headers=headers)
    resp = loads(conn.getresponse().read())
    return resp


def do_download_ciphers(url, savefile):
    save_data = None

    info = get_election_info(url)
    for i, poll in enumerate(info['election']['polls']):
        curr_file = savefile + ".%d" % i
        if exists(curr_file):
            m = "file '%s' already exists, will not overwrite" % (curr_file,)
            sys.stdout.write(m + "\n")
            continue

        conn, headers, base = get_login(url)
        download_url = urlparse(poll['ciphers_url']).path
        conn.request('GET', download_url, headers=headers)
        response = conn.getresponse()
        save_data = response.read()
        with open(curr_file, "w") as f:
            f.write(save_data)

    return save_data


def do_upload_mix(outfile, url):

    if "polls" not in url:
        conn = get_http_connection(url)
        conn.request('GET', conn.path)
        response = conn.getresponse()
        polls = loads(response.read())
        for i, poll in enumerate(polls):
            do_upload_mix("{}.{}".format(outfile, i), poll)
        return

    with open(outfile) as f:
        out_data = f.read()
    conn = get_http_connection(url)
    conn.request('POST', conn.path, body=out_data)
    response = conn.getresponse()
    print(response.status, response.read())


def do_upload_factors(outfile, url):
    poll_index = 0
    curr_file = outfile + ".%d" % poll_index

    while(exists(curr_file)):
        with open(curr_file) as f:
            out_data = f.read()
        info = get_election_info(url)
        path = info['election']['polls'][poll_index]['post_decryption_url']
        path = urlparse(path).path

        conn, headers, redirect = get_login(url)
        body = urlencode({'factors_and_proofs': out_data})
        conn.request('POST', path, body=body, headers=headers)
        response = conn.getresponse().read()
        print(response)

        poll_index += 1
        curr_file = outfile + ".%d" % poll_index


def do_mix(mixfile, newfile, nr_rounds, nr_parallel, module):
    if exists(newfile):
        m = "file '%s' already exists, will not overwrite" % (newfile,)
        raise ValueError(m)

    if os.path.exists("{}.0".format(mixfile)):
        i = 0
        while os.path.exists("{}.{}".format(mixfile, i)):
            do_mix("{}.{}".format(mixfile, i), "{}.{}".format(newfile, i),
                   nr_rounds, nr_parallel, module)
            i = i + 1
        return

    with open(mixfile) as f:
        mix = from_canonical(f)

    new_mix = module.mix_ciphers(mix, nr_rounds=nr_rounds,
                          nr_parallel=nr_parallel)
    with open(newfile, "w") as f:
        to_canonical(new_mix, out=f)

    return new_mix


def do_automix(url, prefix, nr_rounds, nr_parallel, module):
    do_download_mix(url, "{}-votes".format(prefix))
    do_mix("{}-votes".format(prefix), "{}-mix".format(prefix), nr_rounds,
            nr_parallel, module)
    do_upload_mix("{}-mix".format(prefix), url)


def do_decrypt(savefile, outfile, keyfile, nr_parallel):
    poll_index = 0
    curr_file = savefile + ".0"

    with open(keyfile) as f:
        key = load(f)

    secret = int(key['x'])
    pk = key['public_key']
    modulus = int(pk['p'])
    generator = int(pk['g'])
    order = int(pk['q'])
    public = int(pk['y'])
    del key

    while(os.path.isfile(curr_file)):

        curr_outfile = outfile + ".%d" % poll_index
        if exists(curr_outfile):
            m = "file '%s' already exists, will not overwrite" % (curr_outfile,)
            sys.stderr.write(m + "\n")
            poll_index += 1
            curr_file = savefile + ".%d" % poll_index
            continue

        with open(curr_file) as f:
            tally = load(f)['tally']

        ciphers = [(int(ct['alpha']), int(ct['beta']))
                for ct in tally['tally'][0]]
        factors = compute_decryption_factors(modulus, generator, order,
                                            secret, ciphers,
                                            nr_parallel=nr_parallel)
        decryption_factors = []
        factor_append = decryption_factors.append
        decryption_proofs = []
        proof_append = decryption_proofs.append

        for factor, proof in factors:
            factor_append(factor)
            f = {}
            f['commitment'] = {'A': proof[0], 'B': proof[1]}
            f['challenge'] = proof[2]
            f['response'] = proof[3]
            proof_append(f)

        factors_and_proofs = {
            'decryption_factors': [decryption_factors],
            'decryption_proofs': [decryption_proofs]
        }

        with open(curr_outfile, "w") as f:
            dump(factors_and_proofs, f)

        poll_index += 1
        curr_file = savefile + ".%d" % poll_index
    return factors


def main_help():
    usage = ("Usage: {0} generate <nr> <domain> <voters.csv>\n"
             "       {0} masscast <voter_url_file> <plaintexts_file> [nr_threads]\n"
             "       {0} show     <voter_url>\n"
             "       {0} castvote <voter_url> <1st>,<2nd>,... (e.g.)\n"
             "       {0} verify   <vote_signature_file> [randomness [plaintext]]\n"
             "\n"
             "       {0} download mix <url> <input.mix>\n"
             "       {0} mix          [<url> <mix-name>|<input.mix> <output.mix>] <nr_rounds> <nr_parallel>\n"
             "       {0} upload mix   <output.mix> <url>\n"
             "\n"
             "       {0} download ciphers <url> <ballots_savefile>\n"
             "       {0} decrypt          <ballots_savefile> <factors_outfile> <key_file> <nr_parallel>\n"
             "       {0} upload factors   <factors_outfile> <url>\n".format(sys.argv[0]))
    sys.stderr.write(usage)
    raise SystemExit


def main(argv=None):
    argv = argv or sys.argv
    argc = len(argv)
    if argc < 2:
        main_help()

    cmd = argv[1]

    if cmd == 'download':
        if argc < 5:
            main_help()
        if argv[2] == 'mix':
            do_download_mix(argv[3], argv[4])
        elif argv[2] == 'ciphers':
            do_download_ciphers(argv[3], argv[4])
        else:
            main_help()
    elif cmd == 'upload':
        if argc < 5:
            main_help()
        if argv[2] == 'mix':
            do_upload_mix(argv[3], argv[4])
        elif argv[2] == 'factors':
            do_upload_factors(argv[3], argv[4])
        else:
            main_help()
    elif cmd == 'mix':
        if argc < 6:
            main_help()
        from . import zeus_sk as shuffle_module
        if argv[2].startswith("http"):
            do_automix(argv[2], argv[3], int(argv[4]), int(argv[5]),
                shuffle_module)
        else:
            do_mix(argv[2], argv[3], int(argv[4]), int(argv[5]),
                shuffle_module)
    elif cmd == 'decrypt':
        if argc < 6:
            main_help()
        do_decrypt(argv[2], argv[3], argv[4], int(argv[5]))
    elif cmd == 'generate':
        if argc < 5:
            main_help()
        main_generate(int(argv[2]), argv[3], argv[4])
    elif cmd == 'masscast':
        if argc < 4:
            main_help()
        nr_threads=int(argv[4]) if argc > 4 else 2
        main_random_cast(argv[2], argv[3], nr_threads=nr_threads)
    elif cmd == 'show':
        if argc < 3:
            main_help()
        main_show(argv[2])
    elif cmd == 'castvote':
        if argc < 3:
            main_help()
        if argc == 3:
            main_show(argv[2])
        else:
            main_vote(argv[2], ''.join(argv[3:]))
    elif cmd == 'verify':
        if argc < 3:
            main_help()
        randomness = None if argc < 4 else int(argv[3])
        plaintext = None if argc < 5 else int(argv[4])
        main_verify(argv[2], randomness, plaintext)
    else:
        main_help()


if __name__ == '__main__':
    main(sys.argv)
