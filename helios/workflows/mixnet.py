
from hashlib import sha256

from helios.workflows.homomorphic import Tally as HomomorphicTally

# we are extending homomorphic workflow
from helios.workflows.homomorphic import WorkflowObject, DLogTable, EncryptedVote, EncryptedAnswer


TYPE = 'mixnet'


class MixedAnswers(WorkflowObject):

    @property
    def datatype(self):
        return "phoebus/MixedAnswers"

    def __init__(self, answers=[], question_num=0):
        self.answers = answers
        self.question_num = question_num

class MixedAnswer(WorkflowObject):

    @property
    def datatype(self):
        return "phoebus/MixedAnswer"

    def __init__(self, choice=None, index=None):
        self.index = index
        self.choice = choice

    @classmethod
    def fromEncryptedAnswer(cls, answer, index):
        return cls(answer=answer.choice, index=index)


class Tally(HomomorphicTally):

    @property
    def datatype(self):
        return "phoebus/Tally"

    def get_encrypted_votes(self):
        return list(filter(bool, [v.vote for v in self.election.voter_set.all()]))

    def decryption_factors_and_proofs(self, sk):
        """
        returns an array of decryption factors and a corresponding array of decryption proofs.
        makes the decryption factors into strings, for general Helios / JS compatibility.
        """
        # for all choices of all questions (double list comprehension)
        decryption_factors = [[]]
        decryption_proof = [[]]

        for vote in self.tally[0]:
            dec_factor, proof = sk.decryption_factor_and_proof(vote)
            decryption_factors[0].append(dec_factor)
            decryption_proof[0].append(proof)

        return decryption_factors, decryption_proof

    def decrypt_from_factors(self, decryption_factors, public_key):
        """
        decrypt a tally given decryption factors

        The decryption factors are a list of decryption factor sets, for each trustee.
        Each decryption factor set is a list of lists of decryption factors (questions/answers).
        """

        # pre-compute a dlog table
        dlog_table = DLogTable(base = public_key.g, modulus = public_key.p)

        if not self.num_tallied:
            self.num_tallied = len(self.tally[0])

        dlog_table.precompute(self.num_tallied)

        result = []

        # go through each one
        for q_num, q in enumerate(self.tally):
            q_result = []

            for a_num, a in enumerate(q):
            # coalesce the decryption factors into one list
                dec_factor_list = [df[q_num][a_num] for df in decryption_factors]
                raw_value = self.tally[q_num][a_num].decrypt(dec_factor_list, public_key)

                # q_decode
                if raw_value > public_key.q:
                    raw_value = -raw_value % public_key.p
                raw_value = raw_value - 1
                q_result.append(raw_value)

            result.append(q_result)

        return result

class EncryptedVote(EncryptedVote):

    @property
    def datatype(self):
        return "phoebus/EncryptedVote"

    @property
    def encrypted_answer(self):
        return self.encrypted_answers[0]

    def get_cipher(self):
        """
        For one vote there is one cipher.
        """
        return self.encrypted_answers[0].choices[0]

    def verify(self, election):
        # right number of answers
        if len(self.encrypted_answers) != 1:
            return False

        # check hash
        if self.election_hash != election.hash:
            # print "%s / %s " % (self.election_hash, election.hash)
            return False

        # check ID
        if self.election_uuid != election.uuid:
            return False

        if not self.encrypted_answers[0].verify(election.public_key):
            return False

        return True


class EncryptedAnswer(EncryptedAnswer):

    @property
    def datatype(self):
        return "phoebus/EncryptedAnswer"

    def __init__(self, choices=None, encryption_proof=None, randomness=None,
                 answer=None):
        self.choices = choices
        self.randomness = randomness
        self.answer = answer
        self.encryption_proof = encryption_proof

    @property
    def choice(self):
        return self.choices[0]

    def verify(self, pk):
        verified = verify_encryption(pk.p, pk.g, self.choice.alpha,
                                     self.choice.beta, self.encryption_proof)
        return verified


def strbin_to_int(string):
    # lsb
    s = 0
    base = 1
    for c in string:
        s += ord(c) * base
        base *= 256

    return s


def hash_to_commitment_and_challenge(alpha, beta):
    h = sha256()
    h.update(hex(alpha))
    ha = strbin_to_int(h.digest())
    h = sha256()
    h.update(hex(beta))
    hb = strbin_to_int(h.digest())
    commitment = (ha >> 128) | ((hb << 128) & (2**256-1))
    challenge = (hb >> 128) | ((ha << 128) & (2**256-1))

    return commitment, challenge


def verify_encryption(modulus, base, alpha, beta, proof):
    commitment, challenge = hash_to_commitment_and_challenge(alpha, beta)
    return (pow(base, proof, modulus) ==
            (pow(base, commitment, modulus) *
             pow(alpha, challenge, modulus) % modulus))
