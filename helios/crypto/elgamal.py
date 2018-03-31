"""
ElGamal Algorithms for the Helios Voting System

This is a copy of algs.py now made more El-Gamal specific in naming,
for modularity purposes.

Ben Adida
ben@adida.net
"""


import logging


from .algs import Utils
from zeus.core import prove_dlog, prove_ddh_tuple


class Cryptosystem(object):
    def __init__(self):
        self.p = None
        self.q = None
        self.g = None

    @classmethod
    def generate(cls, n_bits):
        """
        generate an El-Gamal environment. Returns an instance
        of ElGamal(), with prime p, group size q, and generator g
        """

        EG = cls()

        # find a prime p such that (p-1)/2 is prime q
        EG.p = Utils.random_safe_prime(n_bits)

        # q is the order of the group
        # FIXME: not always p-1/2
        EG.q = (EG.p-1)//2

        # find g that generates the q-order subgroup
        while True:
            EG.g = Utils.random_mpz_lt(EG.p)
            if pow(EG.g, EG.q, EG.p) == 1:
                break

        return EG

    def generate_keypair(self):
        """
        generates a keypair in the setting
        """

        keypair = KeyPair()
        keypair.generate(self.p, self.q, self.g)

        return keypair


class KeyPair(object):
    def __init__(self):
        self.pk = PublicKey()
        self.sk = SecretKey()

    def generate(self, p, q, g):
        """
        Generate an ElGamal keypair
        """
        self.pk.g = g
        self.pk.p = p
        self.pk.q = q

        self.sk.x = Utils.random_mpz_lt(p)
        self.pk.y = pow(g, self.sk.x, p)

        self.sk.public_key = self.pk


class PublicKey:
    def __init__(self):
        self.y = None
        self.p = None
        self.g = None
        self.q = None

    def encrypt_with_r(self, plaintext, r, encode_message=False):
        """
        expecting plaintext.m to be a big integer
        """
        ciphertext = Ciphertext()
        ciphertext.pk = self

        # make sure m is in the right subgroup
        if encode_message:
            y = plaintext.m + 1
            if pow(y, self.q, self.p) == 1:
                m = y
            else:
                m = -y % self.p
        else:
            m = plaintext.m

        ciphertext.alpha = pow(self.g, r, self.p)
        ciphertext.beta = (m * pow(self.y, r, self.p)) % self.p

        return ciphertext

    def encrypt_return_r(self, plaintext):
        """
        Encrypt a plaintext and return the randomness just generated and used.
        """
        r = Utils.random_mpz_lt(self.q)
        ciphertext = self.encrypt_with_r(plaintext, r)

        return [ciphertext, r]

    def encrypt(self, plaintext):
        """
        Encrypt a plaintext, obscure the randomness.
        """
        return self.encrypt_return_r(plaintext)[0]

    def __mul__(self, other):
        if other == 0 or other == 1:
            return self

        # check p and q
        if self.p != other.p or self.q != other.q or self.g != other.g:
            raise Exception("incompatible public keys")

        result = PublicKey()
        result.p = self.p
        result.q = self.q
        result.g = self.g
        result.y = (self.y * other.y) % result.p
        return result

    def verify_sk_proof(self, dlog_proof, challenge_generator=None):
        """
        verify the proof of knowledge of the secret key
        g^response = commitment * y^challenge
        """
        left_side = pow(self.g, dlog_proof.response, self.p)
        right_side = (dlog_proof.commitment * pow(self.y, dlog_proof.challenge, self.p)) % self.p

        expected_challenge = challenge_generator(dlog_proof.commitment) % self.q

        return ((left_side == right_side) and (dlog_proof.challenge == expected_challenge))


class SecretKey:
    def __init__(self):
        self.x = None
        self.public_key = None

    @property
    def pk(self):
        return self.public_key

    def decryption_factor(self, ciphertext):
        """
        provide the decryption factor, not yet inverted because of needed proof
        """
        return pow(ciphertext.alpha, self.x, self.pk.p)

    def decryption_factor_and_proof(self, ciphertext):
        dec_factor = self.decryption_factor(ciphertext)

        modulus = self.pk.p
        generator = self.pk.g
        order = self.pk.q
        public = self.pk.y
        secret = self.x

        factor = pow(ciphertext.alpha, secret, modulus)
        proof = ZKProof.generate(modulus, generator, order, ciphertext.alpha,
                                 public, factor, secret)

        return factor, proof

    def decrypt(self, ciphertext, dec_factor=None, decode_m=False):
        """
        Decrypt a ciphertext. Optional parameter decides whether to encode the message into the proper subgroup.
        """
        if not dec_factor:
            dec_factor = self.decryption_factor(ciphertext)

        m = (Utils.inverse(dec_factor, self.pk.p) * ciphertext.beta) % self.pk.p

        if decode_m:
            # get m back from the q-order subgroup
            if m < self.pk.q:
                y = m
            else:
                y = -m % self.pk.p

            return Plaintext(y-1, self.pk)
        else:
            return Plaintext(m, self.pk)

    def prove_sk(self):
        res = prove_dlog(self.pk.p, self.pk.g, self.pk.q, self.pk.y, self.x)
        return DLogProof(res[0], res[1], res[2])


class Plaintext:
    def __init__(self, m=None, pk=None):
        self.m = m
        self.pk = pk


class Ciphertext:
    def __init__(self, alpha=None, beta=None, pk=None):
        self.pk = pk
        self.alpha = alpha
        self.beta = beta

    def __mul__(self, other):
        """
        Homomorphic Multiplication of ciphertexts.
        """
        if type(other) == int and (other == 0 or other == 1):
            return self

        if self.pk != other.pk:
            logging.info(self.pk)
            logging.info(other.pk)
            raise Exception('different PKs!')

        new = Ciphertext()

        new.pk = self.pk
        new.alpha = (self.alpha * other.alpha) % self.pk.p
        new.beta = (self.beta * other.beta) % self.pk.p

        return new

    def reenc_with_r(self, r):
        """
        We would do this homomorphically, except
        that's no good when we do plaintext encoding of 1.
        """
        new_c = Ciphertext()
        new_c.alpha = (self.alpha * pow(self.pk.g, r, self.pk.p)) % self.pk.p
        new_c.beta = (self.beta * pow(self.pk.y, r, self.pk.p)) % self.pk.p
        new_c.pk = self.pk

        return new_c

    def reenc_return_r(self):
        """
        Reencryption with fresh randomness, which is returned.
        """
        r = Utils.random_mpz_lt(self.pk.q)
        new_c = self.reenc_with_r(r)
        return [new_c, r]

    def reenc(self):
        """
        Reencryption with fresh randomness, which is kept obscured (unlikely to be useful.)
        """
        return self.reenc_return_r()[0]

    def __eq__(self, other):
        """
        Check for ciphertext equality.
        """
        if other is None:
            return False

        return (self.alpha == other.alpha and self.beta == other.beta)

    def generate_encryption_proof(self, plaintext, randomness, challenge_generator):
        """
        Generate the disjunctive encryption proof of encryption
        """
        # random W
        w = Utils.random_mpz_lt(self.pk.q)

        # build the proof
        proof = ZKProof()

        # compute A=g^w, B=y^w
        proof.commitment['A'] = pow(self.pk.g, w, self.pk.p)
        proof.commitment['B'] = pow(self.pk.y, w, self.pk.p)

        # generate challenge
        proof.challenge = challenge_generator(proof.commitment)

        # Compute response = w + randomness * challenge
        proof.response = (w + (randomness * proof.challenge)) % self.pk.q

        return proof

    def simulate_encryption_proof(self, plaintext, challenge=None):
        # generate a random challenge if not provided
        if not challenge:
            challenge = Utils.random_mpz_lt(self.pk.q)

        proof = ZKProof()
        proof.challenge = challenge

        # compute beta/plaintext, the completion of the DH tuple
        beta_over_plaintext = (self.beta * Utils.inverse(plaintext.m, self.pk.p)) % self.pk.p

        # random response, does not even need to depend on the challenge
        proof.response = Utils.random_mpz_lt(self.pk.q)

        # now we compute A and B
        proof.commitment['A'] = (Utils.inverse(pow(self.alpha, proof.challenge, self.pk.p), self.pk.p) * pow(self.pk.g, proof.response, self.pk.p)) % self.pk.p
        proof.commitment['B'] = (Utils.inverse(pow(beta_over_plaintext, proof.challenge, self.pk.p), self.pk.p) * pow(self.pk.y, proof.response, self.pk.p)) % self.pk.p

        return proof

    def generate_disjunctive_encryption_proof(self, plaintexts, real_index, randomness, challenge_generator):
        # note how the interface is as such so that the result does not reveal which is the real proof.

        proofs = [None for p in plaintexts]

        # go through all plaintexts and simulate the ones that must be simulated.
        for p_num in range(len(plaintexts)):
            if p_num != real_index:
                proofs[p_num] = self.simulate_encryption_proof(plaintexts[p_num])

        # the function that generates the challenge
        def real_challenge_generator(commitment):
            # set up the partial real proof so we're ready to get the hash
            proofs[real_index] = ZKProof()
            proofs[real_index].commitment = commitment

            # get the commitments in a list and generate the whole disjunctive challenge
            commitments = [p.commitment for p in proofs]
            disjunctive_challenge = challenge_generator(commitments)

            # now we must subtract all of the other challenges from this challenge.
            real_challenge = disjunctive_challenge
            for p_num in range(len(proofs)):
                if p_num != real_index:
                    real_challenge = real_challenge - proofs[p_num].challenge

            # make sure we mod q, the exponent modulus
            return real_challenge % self.pk.q

        # do the real proof
        real_proof = self.generate_encryption_proof(plaintexts[real_index], randomness, real_challenge_generator)

        # set the real proof
        proofs[real_index] = real_proof

        return ZKDisjunctiveProof(proofs)

    def verify_encryption_proof(self, plaintext, proof):
        """
        Checks for the DDH tuple g, y, alpha, beta/plaintext.
        (PoK of randomness r.)

        Proof contains commitment = {A, B}, challenge, response
        """

        # check that g^response = A * alpha^challenge
        first_check = (pow(self.pk.g, proof.response, self.pk.p) == ((pow(self.alpha, proof.challenge, self.pk.p) * proof.commitment['A']) % self.pk.p))

        # check that y^response = B * (beta/m)^challenge
        beta_over_m = (self.beta * Utils.inverse(plaintext.m, self.pk.p)) % self.pk.p
        second_check = (pow(self.pk.y, proof.response, self.pk.p) == ((pow(beta_over_m, proof.challenge, self.pk.p) * proof.commitment['B']) % self.pk.p))

        # print "1,2: %s %s " % (first_check, second_check)
        return (first_check and second_check)

    def decrypt(self, decryption_factors, public_key):
        """
        decrypt a ciphertext given a list of decryption factors (from multiple trustees)
        For now, no support for threshold
        """
        running_decryption = self.beta
        for dec_factor in decryption_factors:
            running_decryption = (running_decryption * Utils.inverse(dec_factor, public_key.p)) % public_key.p

        return running_decryption

    def to_string(self):
        return "%s,%s" % (self.alpha, self.beta)

    @classmethod
    def from_string(cls, str):
        """
        expects alpha,beta
        """
        split = str.split(",")
        return cls.from_dict({'alpha': split[0], 'beta': split[1]})


class ZKProof(object):
    def __init__(self):
        self.commitment = {'A': None, 'B': None}
        self.challenge = None
        self.response = None

    @classmethod
    def generate(cls, modulus, generator, order,
                                  alpha, public, factor, secret):
        """
        generate a DDH tuple proof, where challenge generator is
        almost certainly EG_fiatshamir_challenge_generator
        """

        base_commitment, message_commitment, challenge, response = \
            prove_ddh_tuple(modulus, generator, order, alpha, public, factor,
                          secret)
        proof = cls()
        proof.commitment['A'] = base_commitment
        proof.commitment['B'] = message_commitment
        proof.challenge = challenge
        proof.response = response
        return proof


class ZKDisjunctiveProof:
    def __init__(self, proofs=None):
        self.proofs = proofs


class DLogProof(object):
    def __init__(self, commitment=None, challenge=None, response=None):
        self.commitment = commitment
        self.challenge = challenge
        self.response = response
