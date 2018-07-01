# -*- coding: utf-8 -*-

import csv
from functools import partial

from io import StringIO
from zeus.core import gamma_decode
from zeus.utils import CSVReader
from django.db.models import Count
from django.utils.translation import ugettext as _
from django.utils import translation

from collections import OrderedDict


def zeus_report(elections):
    from helios.models import CastVote, Voter
    return {
        'elections': elections,
        'votes': CastVote.objects.filter(election__in=elections, voter__excluded_at__isnull=True).count(),
        'voters': Voter.objects.filter(election__in=elections).count(),
        'voters_cast': CastVote.objects.filter(election__in=elections,
                                         voter__excluded_at__isnull=True).distinct('voter').count()
    }


SENSITIVE_DATA = ['admin_user', 'trustees', 'last_view_at']


def election_report(elections, votes_report=True, filter_sensitive=True):
    for e in elections:
        entry = OrderedDict([
            ('name', e.name),
            ('uuid', e.uuid),
            ('admin_user', e.admins.filter().values('user_id',
                                                        'ecounting_account')[0]),
            ('institution', e.institution.name),
            ('voting_started_at', e.voting_starts_at),
            ('voting_ended_at', e.voting_ended_at),
            ('voting_extended', bool(e.voting_extended_until)),
            ('voting_extended_until', e.voting_extended_until),
            ('voting_ends_at', e.voting_ends_at),
            ('trustees', list(e.trustees.filter().no_secret().values('name', 'email'))),
        ])
        if votes_report:
            voters_added = e.voters.count()
            entry.update(OrderedDict([
                ('excluded_count', e.voters.filter(excluded_at__isnull=False).count()),
                ('audit_requests_count', e.audits.filter().requests().count()),
                ('audit_cast_count', e.audits.filter().confirmed().count()),
                ('voters_count', e.voters.count()),
                ('voters_cast_count', e.casts.filter().countable().distinct('voter').count()),
                ('excluded_voters_cast_count', e.casts.filter().excluded().distinct('voter').count()),
                ('cast_count', e.casts.count()),
                ('voters_visited_count', e.voters.filter().visited().count()),
                ('last_view_at', e.voters.order_by('-last_visit')[0].last_visit if voters_added else None)
            ]))

        if filter_sensitive:
            for key in [k for k in entry if k in SENSITIVE_DATA]:
                del entry[key]

        yield entry


def election_votes_report(elections, include_alias=False, filter_sensitive=True):
    from helios.models import CastVote, Voter
    for vote in CastVote.objects.filter(poll__election__in=elections,
                                    voter__excluded_at__isnull=True).values('voter__alias', 'voter',
                                                                           'cast_at').order_by('-cast_at'):
        entry = OrderedDict([
        ])
        if include_alias:
            entry['name'] = vote['voter__alias'],
        if not filter_sensitive:
            entry['name'] = Voter.objects.get(pk=vote['voter']).full_name
        if len(elections) > 1:
            entry['poll'] = vote.poll.name

        entry['date'] = vote['cast_at']
        yield entry


def election_voters_report(elections):
    from helios.models import Voter
    for voter in Voter.objects.filter(poll__election__in=elections,
                                      excluded_at__isnull=True).annotate(cast_count=Count('cast_votes')).order_by('voter_surname'):
        entry = OrderedDict([
            ('name', voter.voter_name),
            ('surname', voter.voter_surname),
            ('fathername', voter.voter_fathername),
            ('email', voter.voter_email),
            ('visited', bool(voter.last_visit)),
            ('votes_count', voter.cast_count)
        ])
        if len(elections) > 1:
            entry['election'] = voter.election.name
        yield entry


def _single_votes(results, clen):
    return [sel for sel in results if len(gamma_decode(sel, clen)) == 1]


def _get_choices_sums(results, choices_len):
    data = OrderedDict()
    for i in range(choices_len+1):
        data[str(i)] = 0

    for encoded in results:
        chosen_len = len(gamma_decode(encoded, choices_len))
        data[str(chosen_len)] = data[str(chosen_len)] + 1

    return data


def election_results_report(elections):
    for election in elections:
        for poll in election.polls.all():
            if not poll.result:
                entry = {}
            else:
                entry = OrderedDict([
                    ('choices', len(poll.questions[0]['answers'])),
                    ('protest_votes_count', poll.result[0].count(0)),
                    ('total_count', len(poll.result[0])),
                    ('choices_sums', _get_choices_sums(poll.result[0],
                                                       len(poll.questions[0]['answers'])))
                ])
            if len(elections) > 1:
                entry['election'] = election.name
                entry['poll'] = poll.election.name
        yield entry


def make_csv_intro(writerow, election, lang):
    with translation.override(lang):
        DATE_FMT = "%d/%m/%Y %H:%M"
        voting_start = election.voting_starts_at.strftime(DATE_FMT)
        voting_end = election.voting_ends_at.strftime(DATE_FMT)
        extended_until = ""
        if election.voting_extended_until:
            extended_until = election.voting_extended_until.strftime(DATE_FMT)
        writerow([str(_("Election name")), str(election.name)])
        writerow([str(_("Institution name")), str(election.institution.name)])
        writerow([str(_("Start")), str(voting_start)])
        writerow([str(_("End")), str(voting_end)])
        if extended_until:
            writerow([str(_("Extension")), str(extended_until)])
        writerow([])
        nr_voters = election.voters.all().count()
        writerow([str(_("Voters")), str(nr_voters)])
        if election.voters.all().excluded().count() > 0:
            ex_voters = election.voters.all().excluded().count()
            writerow([str(_("Excluded voters")), str(ex_voters)])
        writerow([])


def csv_from_polls(election, polls, lang, outfile=None):
    with translation.override(lang):
        if outfile is None:
            outfile = StringIO()
        csvout = csv.writer(outfile, dialect='excel', delimiter=',')
        writerow = csvout.writerow
        make_csv_intro(writerow, election, lang)
        for poll in polls:
            party_results = poll.zeus.get_results()
            invalid_count = party_results['invalid_count']
            blank_count = party_results['blank_count']
            ballot_count = party_results['ballot_count']

            writerow([])
            writerow([])
            writerow([])
            writerow([str(_("Poll name")), str(poll.name)])
            writerow([])
            writerow([])
            nr_voters = poll.voters.all().count()
            writerow([str(_("Voters")), str(nr_voters)])
            if poll.voters.all().excluded().count() > 0:
                ex_voters = poll.voters.all().excluded().count()
                writerow([str(_("Excluded voters")), str(ex_voters)])
            writerow([])
            writerow([str(_('RESULTS'))])
            writerow([str(_('TOTAL VOTES')), str(ballot_count)])
            writerow([str(_('VALID VOTES')), str(ballot_count - invalid_count)])
            writerow([str(_('INVALID VOTES')), str(invalid_count)])
            writerow([str(_('BLANK VOTES')), str(blank_count)])

            writerow([])
            writerow([str(_('PARTY RESULTS'))])
            for count, party in party_results['party_counts']:
                if party is None:
                    continue
                party = party.replace("{newline}", " ")
                writerow([str(party), str(count)])

            writerow([])
            writerow([str(_('CANDIDATE RESULTS'))])
            for count, candidate in party_results['candidate_counts']:
                writerow([str(candidate), str(count)])

            writerow([])
            writerow([str(_('BALLOTS'))])
            writerow([str(_('ID')), str(_('PARTY')),
                str(_('CANDIDATE')), str(_('VALID/INVALID/BLANK'))])
            counter = 0
            valid = str(_('VALID'))
            invalid = str(_('INVALID'))
            blank = str(_('BLANK'))
            empty = '---'
            for ballot in party_results['ballots']:
                party = empty
                counter += 1
                if not ballot['valid']:
                    writerow([counter, empty, empty, invalid])
                    continue
                ballot_parties = ballot['parties']
                if not ballot_parties:
                    writerow([counter, empty, empty, blank])
                else:
                    for party in ballot_parties:
                        if party is None:
                            writerow([counter, empty, empty, empty])
                            continue
                        else:
                            party = str(party)

                candidates = ballot['candidates']
                if not candidates:
                    writerow([counter, party, empty, valid])
                    continue

                for candidate in candidates:
                    writerow([counter, party, str(": ".join(candidate)), valid])


def csv_from_stv_polls(election, polls, lang, outfile=None):
    with translation.override(lang):
        if outfile is None:
            outfile = StringIO()
        csvout = csv.writer(outfile, dialect='excel', delimiter=',')
        writerow = csvout.writerow

        make_csv_intro(writerow, election, lang)
        actions_desc = {
            'elect': _('Elect'),
            'eliminate': _('Eliminated'),
            'quota': _('Eliminated due to quota restriction')}
        from stv.parser import STVParser
        for poll in polls:
            writerow([])
            writerow([str(_("Poll name")), str(poll.name)])
            writerow([])
            questions = poll.questions
            indexed_cands = {}
            counter = 0
            for item in questions[0]['answers']:
                indexed_cands[str(counter)] = item
                counter += 1

            results_winners = poll.stv_results[0]
            result_steps = poll.stv_results[2]
            stv = STVParser(result_steps)
            rounds = list(stv.rounds())
            writerow([])
            writerow([str(_("Elected")), str(_("Departments"))])
            for winner_data in results_winners:
                winner_id = winner_data[0]
                winner = indexed_cands[str(winner_id)]
                winner = winner.split(':')
                winner_name = winner[0]
                winner_department = winner[1]
                writerow([str(winner_name), str(winner_department)])
            for num, round in rounds:
                round_name = _('Round ')
                round_name +=str(num)
                writerow([])
                writerow([str(round_name)])
                writerow([str(_('Candidate')), str(_('Votes')),
                    str(_('Draw')), str(_('Action'))])
                for name, cand in round['candidates'].items():
                    actions = [x[0] for x in cand['actions']]
                    actions = [x[0] for x in cand['actions']]
                    draw = _("NO")
                    if 'random' in actions:
                        draw = _("YES")
                    action = None
                    if len(actions):
                        action = actions_desc.get(actions[-1])
                    votes = cand['votes']
                    cand_name = indexed_cands[str(name)]
                    cand_name = cand_name.split(':')[0]
                    writerow([str(cand_name), str(votes),
                    str(draw), str(action)])


def csv_from_score_polls(election, polls, lang, outfile=None):
    with translation.override(lang):
        if outfile is None:
            outfile = StringIO()
        csvout = csv.writer(outfile, dialect='excel', delimiter=',')
        writerow = csvout.writerow
        make_csv_intro(writerow, election, lang)

        for poll in polls:
            score_results = poll.zeus.get_results()
            invalid_count = len([b for b in score_results['ballots']
                                if not b['valid']])
            blank_count = len([b for b in score_results['ballots']
                            if not b.get('candidates')])
            ballot_count = len(score_results['ballots'])

            writerow([])
            writerow([])
            writerow([])
            writerow([str(poll.name)])
            writerow([])
            writerow([])
            writerow([str(_('RESULTS'))])
            writerow([str(_('TOTAL VOTES')), str(ballot_count)])
            writerow([str(_('VALID VOTES')), str(ballot_count - invalid_count)])
            writerow([str(_('INVALID VOTES')), str(invalid_count)])
            writerow([str(_('BLANK VOTES')), str(blank_count)])

            writerow([])
            writerow([str(_('RANKING'))])
            for score, candidate in sorted(score_results['totals']):
                candidate = candidate.replace("{newline}", " ")
                writerow([str(score), str(candidate)])

            writerow([])
            writerow([str(_('SCORES'))])
            pointlist = list(sorted(score_results['points']))
            pointlist.reverse()
            writerow([str(_('CANDIDATE')), str(_('SCORES:'))] + pointlist)
            for candidate, points in sorted(score_results['detailed'].items()):
                writerow([str(candidate), ''] +
                        [str(points[p]) for p in pointlist])

            writerow([])
            writerow([str(_('BALLOTS'))])
            writerow([str(_('ID')), str(_('CANDIDATE')),
                str(_('SCORES')), str(_('VALID/INVALID/BLANK'))])
            counter = 0
            valid = str(_('VALID'))
            invalid = str(_('INVALID'))
            empty = '---'
            for ballot in score_results['ballots']:
                counter += 1
                if not ballot['valid']:
                    writerow([counter, empty, empty, invalid])
                    continue
                points = sorted(ballot['candidates'].items())
                for candidate, score in points:
                    candidate = candidate.replace("{newline}", " ")
                    writerow([str(counter), str(candidate),
                            str(score), valid])


class ElectionsReport(object):
    def __init__(self, elections):
        self.elections = elections
        self.objectData = []
        self.header = [_("Institution"),
                       _("Electors"),
                       _("Voters"),
                       _("Start"),
                       _("End"),
                       _("uuid"),
                       _("Name"),
                       _("Polls"),
                       _("Administrator"),
                       _("Official"), ]

    def get_elections(self):
        return self.elections

    def set_elections(self, election_list):
        self.elections = election_list

    def append_elections(self, election_list):
        self.elections += election_list

    def parse_object(self):
        data = []
        for e in self.elections:
            row = {}
            row['inst'] = e.institution.name
            row['nr_voters'] = e.voters.count()
            row['nr_voters_voted'] = e.voters.cast().count()
            start = e.voting_starts_at
            start = start.strftime("%Y-%m-%d %H:%M") if start else ''
            end = e.voting_ended_at
            end = end.strftime("%Y-%m-%d %H:%M") if end else ''
            row['start'] = start
            row['end'] = end
            row['uuid'] = e.uuid
            row['election_name'] = e.name
            row['nr_polls'] = e.polls.count()
            admins = [admin.user_id for admin in e.admins.all()]
            admins = ",".join(map(str, admins))
            row['admin'] = admins
            if e.official == 0:
                row['official'] = 'Unofficial'
            elif e.official == 1:
                row['official'] = 'Official'
            else:
                row['official'] = 'Not Decided'
            data.append(row)
        self.objectData += data


class ElectionsReportCSV(ElectionsReport):
    '''
    Create CSV with data from all elections that
    are marked as suitable for reporting.
    Includes CSV file if set in settings.
    '''

    def __init__(self, elections):
        super(ElectionsReportCSV, self).__init__(elections)
        self.csvData = []

    def parse_csv(self, csv_file_path):
        data = []
        with open(csv_file_path, 'rb') as f:
            reader = CSVReader(f, min_fields=2, max_fields=10)
            for row in reader:
                keys = ('inst', 'nr_voters', 'nr_voters_voted', 'start',
                        'end', 'uuid', 'election_name', 'admin', 'official')
                new_row = {}
                for index, key in enumerate(keys):
                    new_row[key] = row[index]
                new_row['nr_polls'] = '-'
                data.append(new_row)
        self.csvData += data

    def make_output(self, filename):
        data = self.csvData + self.objectData
        keys = ('inst', 'nr_voters', 'nr_voters_voted', 'start',
                'end', 'uuid', 'election_name', 'nr_polls', 'admin', 'official')

        fd = filename
        close = False
        if isinstance(filename, str):
            fd = open("{}.csv".format(filename), 'wb')
            close = True

        writer = csv.writer(fd, delimiter=',')
        writer.writerow(self.header)
        for row in data:
            writer.writerow(row[k] for k in keys)
        if close:
            fd.close()


def csv_from_unigovgr_results(election, results, lang, outfile=None):
    with translation.override(lang):
        if outfile is None:
            outfile = StringIO()
        csvout = csv.writer(outfile, dialect='excel', delimiter=',')
        writerow = csvout.writerow
        make_csv_intro(writerow, election, lang)

        def get(g, key):
            keys = key.split('.')
            obj = results[g]
            while len(keys):
                obj = obj[keys.pop(0)]
            return obj

        T = partial(get, 'totals')
        A = partial(get, 'group_a')
        B = partial(get, 'group_b')

        def ROW(label, key):
            return [str(label), str(T(key)), str(A(key)), str(B(key))]

        writerow([])
        writerow([])
        writerow([])
        writerow([])
        writerow([])
        writerow(['', str(_("Total")), str(A('name')), str(B('name'))])
        writerow(ROW(_("Voters"), 'voters'))
        if T('excluded') > 0:
            writerow(ROW(_("Excluded voters"), 'excluded'))
        writerow([])
        writerow([str(_('RESULTS'))])
        writerow(ROW(_('TOTAL VOTES'), 'voted'))
        writerow(ROW(_('VALID VOTES'), 'valid'))
        writerow(ROW(_('INVALID VOTES'), 'invalid'))
        writerow(ROW(_('BLANK VOTES'), 'blank'))

        writerow([])
        writerow([str(_('RESULTS'))])
        for question, answers in list(T('counts').items()):
            writerow([])
            writerow([str(question)])
            writerow(['', str(_("Total rounded")), str(_("Total")), str(A('name')), str(B('name'))])
            for answer in answers:
                key = 'counts.%s.%s' % (question, answer)
                key_round = 'counts_rounded.%s.%s' % (question, answer)
                writerow([
                    str(answer),
                    str(T(key_round)),
                    str(T(key)),
                    str(A(key)),
                    str(B(key))
                ])

        writerow([])
        writerow([str(_('BALLOTS'))])
        writerow([str(_('GROUP')), str(_('ID')), str(_('QUESTION')),
            str(_('CANDIDATE')), str(_('VALID/INVALID/BLANK'))])
        counter = 0
        valid = str(_('VALID'))
        invalid = str(_('INVALID'))
        blank = str(_('BLANK'))
        empty = '---'
        for ballot in T('ballots'):
            unigov_group = str(ballot['unigov_group'])
            party = empty
            counter += 1
            if not ballot['valid']:
                writerow([unigov_group, counter, empty, empty, invalid])
                continue
            ballot_parties = ballot['parties']
            if not ballot_parties:
                writerow([unigov_group, counter, empty, empty, blank])
            else:
                for party in ballot_parties:
                    if party is None:
                        writerow([unigov_group, counter, empty, empty, empty])
                        continue
                    else:
                        party = str(party)

            candidates = ballot['candidates']
            if not candidates:
                writerow([unigov_group, counter, party, empty, valid])
                continue

            for candidate in candidates:
                writerow([unigov_group, counter, party, str(": ".join(candidate)), valid])
