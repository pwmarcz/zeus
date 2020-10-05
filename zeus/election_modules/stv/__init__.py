
import json
import logging
import io

from django.utils.translation import gettext_lazy as _
from django.forms.formsets import formset_factory
from django.conf import settings

from zeus.election_modules import ElectionModuleBase, election_module

from stv.stv import count_stv, Ballot
from zeus.core import gamma_decode, to_absolute_answers


@election_module
class StvElection(ElectionModuleBase):
    module_id = 'stv'
    description = _('Single transferable vote election')
    messages = {
        'answer_title': _('Candidate'),
        'question_title': _('Candidates List')
    }
    auto_append_answer = True
    count_empty_question = False
    booth_questions_tpl = 'question_ecounting'
    no_questions_added_message = _('No questions set')
    manage_questions_title = _('Manage questions')
    module_params = {
        'ranked': True
    }

    max_questions_limit = 1

    results_template = "election_modules/stv/results.html"

    pdf_result = True
    csv_result = True
    json_result = True

    def questions_update_view(self, request, election, poll):
        if not poll.questions_data:
            poll.questions_data = [{}]

        poll.questions_data[0]['departments_data'] = election.departments
        return super().questions_update_view(request, election, poll)

    def questions_formset(self, extra):
        from zeus.forms import StvForm
        return formset_factory(StvForm, extra=extra,
                               can_delete=True, can_order=True)

    def extract_question_data(self, questions):
        questions_data = []

        for question in questions:
            if not question:
                continue
            # force sort of answers by extracting index from answer key.
            # cast answer index to integer, otherwise answer_10 would
            # be placed before answer_2
            answer_index = lambda a: int(a[0].replace('answer_', ''))
            isanswer = lambda a: a[0].startswith('answer_')

            answer_values = list(filter(isanswer, iter(question.items())))
            sorted_answers = sorted(answer_values, key=answer_index)

            answers = [json.loads(x[1])[0] for x in sorted_answers]
            departments = [json.loads(x[1])[1] for x in sorted_answers]

            final_answers = []
            for a, d in zip(answers, departments):
                final_answers.append(a+':'+d)
            question['answers'] = final_answers
            for k in list(question.keys()):
                if k in ['DELETE', 'ORDER']:
                    del question[k]

            questions_data.append(question)
        return questions_data

    def update_poll_params(self, poll, cleaned_data):
        poll.eligibles_count = int(cleaned_data[0]['eligibles'])
        poll.has_department_limit = cleaned_data[0]['has_department_limit']
        poll.department_limit = int(cleaned_data[0]['department_limit'])

    def update_answers(self):
        answers = []
        questions_data = self.poll.questions_data or []
        prepend_empty_answer = True
        if self.auto_append_answer:
            prepend_empty_answer = True
        for index, q in enumerate(questions_data):
            q_answers = ["%s" % (ans) for ans in
                         q['answers']]
            group = index
            if prepend_empty_answer:
                #remove params and q questions
                params_max = len(q_answers)
                params_min = 0
                if self.count_empty_question:
                    params_min = 0
                params = "%d-%d, %d" % (params_min, params_max, group)
                q_answers.insert(0, "%s: %s" % (q.get('question'), params))
            answers = answers + q_answers
        answers = questions_data[0]['answers']
        self.poll._init_questions(len(answers))
        self.poll.questions[0]['answers'] = answers

    def generate_result_docs(self, lang):
        poll_data = [
            (self.poll.name, self.poll.zeus.get_results(), self.poll.questions,
             self.poll.voters.all())
            ]
        from zeus.results_report import build_stv_doc
        build_stv_doc(_('Results'), self.election.name,
                    self.election.institution.name,
                    self.election.voting_starts_at, self.election.voting_ends_at,
                    self.election.voting_extended_until,
                    poll_data,
                    lang,
                    self.get_poll_result_file_path('pdf', 'pdf', lang[0]))

    def generate_election_result_docs(self, lang):
        from zeus.results_report import build_stv_doc
        polls_data = []

        for poll in self.election.polls.filter():
            polls_data.append((poll.name, poll.zeus.get_results(), poll.questions, poll.voters.all()))

        build_stv_doc(_('Results'), self.election.name,
            self.election.institution.name,
            self.election.voting_starts_at, self.election.voting_ends_at,
            self.election.voting_extended_until,
            polls_data,
            lang,
            self.get_election_result_file_path('pdf', 'pdf', lang[0]))

    def compute_election_results(self):
        for lang in settings.LANGUAGES:
            self.generate_election_result_docs(lang)
            self.generate_election_csv_file(lang)
            self.generate_election_zip_file(lang)

    def compute_results(self):

        cands_data = self.poll.questions_data[0]['answers']
        constituencies = {}
        count_id = 0

        for item in cands_data:
            cand_and_dep = item.split(':')
            constituencies[str(count_id)] = cand_and_dep[1]
            count_id += 1

        seats = self.poll.eligibles_count
        droop = True
        rnd_gen = None # TODO: should be generated and stored on poll freeze
        if self.poll.has_department_limit:
            quota_limit = self.poll.department_limit
        else:
            quota_limit = 0

        ballots = []
        for ballot in get_csv_ballots(self.poll):
            ballot = [str(i) for i in ballot]
            ballots.append(Ballot(ballot))

        stv_stream = io.StringIO()
        stv_logger = logging.Logger(self.poll.uuid)
        handler = logging.StreamHandler(stv_stream)
        stv_logger.addHandler(handler)
        stv_logger.setLevel(logging.DEBUG)
        results = count_stv(ballots, seats, droop, constituencies, quota_limit,
                            rnd_gen, logger=stv_logger)
        results = list(results[0:2])
        handler.close()
        stv_stream.seek(0)
        results.append(stv_stream.read())
        stv_stream.close()
        self.poll.stv_results = results
        self.poll.save()

        # build docs
        self.generate_json_file()
        for lang in settings.LANGUAGES:
            #self.generate_csv_file(lang)
            self.generate_result_docs(lang)
            self.generate_csv_file(lang)

    def get_booth_template(self, request):
        raise NotImplementedError


def get_csv_ballots(poll):
    cands_data = poll.questions_data[0]['answers']
    cands_count = len(cands_data)

    ballots_data = poll.result[0]
    ballots = []
    for ballot in ballots_data:
        if not ballot:
            continue
        ballot = to_absolute_answers(gamma_decode(ballot, cands_count, cands_count),
                                     cands_count)
        ballots.append(ballot)
    return ballots
