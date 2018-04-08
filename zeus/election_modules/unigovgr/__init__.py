# -- coding: utf-8 --

import copy
import math
from decimal import Decimal

from functools import partial
from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from django.forms.formsets import formset_factory
from django.conf import settings

from zeus.election_modules import election_module
from zeus.utils import election_reverse
from zeus.reports import csv_from_unigovgr_results

from zeus.election_modules.simple import SimpleElection
from zeus.election_modules import PollHooks, ElectionHooks


class UniElectionHooks(ElectionHooks):

    def post_create(self, election):
        # create the two polls
        poll = election.polls.create(
            name=str(_("Electors: Group A")),
            oauth2_type='',
            oauth2_code_url='',
            oauth2_client_secret='',
            oauth2_client_type='',
            oauth2_confirmation_url='',
            oauth2_exchange_url='',
            oauth2_client_id='',
            jwt_public_key=''

        )
        election.polls.create(name=str(_("Electors: Group B")))
        return election_reverse(election, 'polls_list')


class UniPollHooks(PollHooks):
    pass


def UNIGOV_ROUND(result):
    return math.floor(result) if ((result - math.floor(result)) < 0.5) else math.ceil(result)


def UNIGOV_COUNT(A, B, G, S, weight=0.2):
    result = A + (
        Decimal((S * B * weight) / G)
    )
    return result, UNIGOV_ROUND(float(result))


class UniGovGrResults():

    def __init__(self, poll_a, poll_b):
        self.group_a = poll_a
        self.group_b = poll_b
        self.questions = OrderedDict()
        for q in self.group_a.questions_data:
            self.questions[q['question']] = q['answers']

    def compute(self):
        results = {
            'group_a': {},
            'group_b': {},
            'totals': {}
        }

        for g in ['totals', 'group_a', 'group_b']:
            results[g]['counts'] = OrderedDict()
            results[g]['counts_rounded'] = OrderedDict()
            for question, answers in self.questions.items():
                results[g]['counts'][question] = {}
                results[g]['counts_rounded'][question] = {}
                for answer in answers:
                    results[g]['counts'][question][answer] = 0
                    results[g]['counts_rounded'][question][answer] = 0

        totals = results['totals']
        for g in ['group_a', 'group_b']:
            poll = getattr(self, g)
            group = results[g]
            group['voters'] = poll.voters.filter().not_excluded().count()
            group['excluded'] = poll.voters.filter().excluded().count()
            group['name'] = poll.name

            zeus_results = poll.zeus.get_results()
            counts = zeus_results['candidate_counts']
            for count, choice in counts:
                question, answer = choice.split(': ', 1)
                group['counts'][question][answer] = count
            group['voted'] = zeus_results['ballot_count']
            group['invalid'] = zeus_results['invalid_count']
            group['valid'] = zeus_results['ballot_count'] - zeus_results['invalid_count']
            group['blank'] = zeus_results['blank_count']
            group['ballots'] = zeus_results['ballots']
            for ballot in group['ballots']:
                ballot['unigov_group'] = g.split('_')[1].upper()

        totals = results['totals']
        group_a = results['group_a']
        group_b = results['group_b']
        for q, candidates in list(totals['counts'].items()):
            for candidate in candidates:
                # ο αριθμός των έγκυρων ψήφων που έλαβε ο κάθε υποψήφιος από τα μέλη της πρώτης ομάδας εκλεκτόρων
                A = group_a['counts'][q][candidate]
                # το σύνολο των μελών της πρώτης ομάδας εκλεκτόρων (ήτοι των μελών Δ.Ε.Π.)
                S = group_a['voters']
                # ο αριθμός των έγκυρων ψήφων που έλαβε ο κάθε υποψήφιος από τη δεύτερη ομάδα εκλεκτόρων
                B = group_b['counts'][q][candidate]
                # Γ: το σύνολο των μελών της δεύτερης ομάδας εκλεκτόρων
                G = group_b['voters']
                if G == 0:
                    result, rounded = -1, -1
                else:
                    result, rounded = UNIGOV_COUNT(A, B, G, S)
                totals['counts'][q][candidate] = result
                totals['counts_rounded'][q][candidate] = rounded

        for key in ['voted', 'blank', 'valid', 'invalid', 'ballots', 'voters', 'excluded']:
            totals[key] = group_a[key] + group_b[key]

        return results

    def questions_formset(self, extra=1):
        from zeus.forms import QuestionForm
        return formset_factory(QuestionForm, extra=extra,
                               can_delete=True, can_order=True)


@election_module
class UniGovGr(SimpleElection):

    module_id = 'unigovgr'
    description = _('Greek Universities single governing bodies election')

    election_hooks_cls = UniElectionHooks
    poll_hooks_cls = UniPollHooks
    booth_module_id = 'simple'
    pdf_result = True
    csv_result = True

    display_poll_results = False
    election_results_partial = "election_modules/unigovgr/election_results.html"

    def compute_results(self):
        self.generate_json_file()
        for lang in settings.LANGUAGES:
            self.generate_csv_file(lang)

    def _count_election_results(self):
        poll_a = self.election.polls.order_by('name')[0]
        poll_b = self.election.polls.order_by('name')[1]
        result = UniGovGrResults(poll_a, poll_b)
        return result.compute()

    def generate_election_csv_file(self, results, lang):
        csvpath = self.get_election_result_file_path('csv', 'csv', lang[0])
        with open(self.get_election_result_file_path('csv', 'csv', lang[0]), "w") as f:
            csv_from_unigovgr_results(self.election, results, lang[0], f)

    def compute_election_results(self):
        results = self._count_election_results()
        for lang in settings.LANGUAGES:
            self.generate_election_csv_file(results, lang)
            self.generate_election_result_docs(results, lang)
            self.generate_election_zip_file(lang)

    def questions_update_view(self, request, election, poll):
        _super = super(UniGovGr, self).questions_update_view
        update_view = partial(_super, request, election)
        siblings = election.polls.filter().exclude(pk=poll.pk)
        for sibling in siblings:
            update_view(sibling)
        return update_view(poll)

    def get_voters_list_headers(self, request=None):
        super_headers = super(UniGovGr, self).get_voters_list_headers(request)
        headers = copy.copy(super_headers)
        is_manager = request and request.zeususer.is_manager

        new_headers = OrderedDict()
        for key, val in headers.items():
            if key in ['last_visit', 'cast_votes__id'] and not is_manager:
                continue
            if key == 'actions' and not is_manager:
                new_headers['excluded_at'] = _('Voter excluded')
            new_headers[key] = val
        return new_headers

    def can_delete_poll_voters(self):
        return not self.election.feature_voting_started

    def can_edit_polls(self):
        return self.election.polls.count() < 2

    def generate_election_result_docs(self, results, lang):
        from zeus.results_report import build_unigov_doc
        results = self._count_election_results()
        pdfpath = self.get_election_result_file_path('pdf', 'pdf', lang[0])
        build_unigov_doc(_('Results'), self.election.name,
                  self.election.institution.name,
                  self.election.voting_starts_at, self.election.voting_ends_at,
                  self.election.voting_extended_until, results, lang,
                  pdfpath)
