"""
Crypto Algorithms for the Helios Voting System

FIXME: improve random number generation.

Ben Adida
ben@adida.net
"""

import math
import randpool
import number


# some utilities
class Utils:
    RAND = randpool.RandomPool()

    @classmethod
    def random_mpz_lt(cls, max):
        # return randrange(0, max)
        n_bits = int(math.floor(math.log(max, 2)))
        return (number.getRandomNumber(n_bits, cls.RAND.get_bytes) % max)

    @classmethod
    def random_prime(cls, n_bits):
        return number.getPrime(n_bits, cls.RAND.get_bytes)

    @classmethod
    def is_prime(cls, mpz):
        return number.isPrime(mpz)

    @classmethod
    def inverse(cls, mpz, mod):
        # return cls.xgcd(mpz,mod)[0]
        return number.inverse(mpz, mod)

    @classmethod
    def random_safe_prime(cls, n_bits):
        p = None
        q = None

        while True:
            p = cls.random_prime(n_bits)
            q = (p-1)/2
            if cls.is_prime(q):
                return p
