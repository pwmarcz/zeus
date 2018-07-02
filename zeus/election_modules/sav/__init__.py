from django.utils.translation import ugettext_lazy as _
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from fractions import Fraction

from zeus.election_modules import ElectionModuleBase, election_module
from zeus.views.utils import set_menu
from django.conf import settings

from helios.view_utils import render_template
from zeus.core import gamma_decode, to_absolute_answers


@election_module
class SavElection(ElectionModuleBase):

    module_id = 'sav'
    description = _('Satisfaction Approval Voting')
    messages = {}
    auto_append_answer = True
    count_empty_question = False
    booth_questions_tpl = ''
    no_questions_added_message = _('No questions set')
    manage_questions_title = _('Manage questions')

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

            answers = [x[1] for x in sorted_answers]
            question['answers'] = answers
            for k in list(question.keys()):
                if k in ['DELETE', 'ORDER']:
                    del question[k]

            questions_data.append(question)
        return questions_data

    def questions_update_view(self, request, election, poll):
        from zeus.utils import poll_reverse
        from zeus.forms import SavForm, DEFAULT_ANSWERS_COUNT

        if not poll.questions_data:
            poll.questions_data = [{}]

        extra = 1
        if poll.questions_data:
            extra = 0

        questions_formset = formset_factory(SavForm, extra=extra,
                                            can_delete=True, can_order=True)

        if request.method == 'POST':
            formset = questions_formset(request.POST)
            if formset.is_valid():
                questions_data = []
                for question in formset.cleaned_data:
                    if not question:
                        continue

                    # force sort of answers by extracting index from answer key.
                    # cast answer index to integer, otherwise answer_10 would
                    # be placed before answer_2
                    answer_index = lambda a: int(a[0].replace('answer_', ''))
                    isanswer = lambda a: a[0].startswith('answer_')
                    answer_values = list(filter(isanswer, iter(question.items())))
                    sorted_answers = sorted(answer_values, key=answer_index)

                    question['answers'] = [x[1] for x in sorted_answers]

                    for k in list(question.keys()):
                        if k in ['DELETE', 'ORDER']:
                            del question[k]

                    questions_data.append(question)

                poll.questions_data = questions_data
                poll.update_answers()
                poll.logger.info("Poll ballot updated")
                poll.save()

                url = poll_reverse(poll, 'questions')
                return HttpResponseRedirect(url)
        else:
            formset = questions_formset(initial=poll.questions_data)

        context = {
            'default_answers_count': DEFAULT_ANSWERS_COUNT,
            'formset': formset,
            'max_questions_limit': 1,
            'election': election,
            'poll': poll,
            'module': self
        }
        set_menu('questions', context)

        tpl = 'election_modules/sav/election_poll_questions_manage'
        return render_template(request, tpl, context)

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

    def compute_results(self):

        for lang in settings.LANGUAGES:
            self.generate_result_docs(lang)
            self.generate_csv_file(lang)

    def compute_election_results(self):
        for lang in settings.LANGUAGES:
            # self.generate_election_result_docs(lang)
            self.generate_election_csv_file(lang)

    def generate_result_docs(self, lang):
        poll_data = [
            (self.poll.name, count_sav_results(self.poll), self.poll.questions,
             self.poll.voters.all())
            ]
        from zeus.results_report import build_sav_doc
        build_sav_doc(_('Results'), self.election.name,
                    self.election.institution.name,
                    self.election.voting_starts_at, self.election.voting_ends_at,
                    self.election.voting_extended_until,
                    poll_data,
                    lang,
                    self.get_poll_result_file_path('pdf', 'pdf', lang[0]))


def count_sav_results(poll):
    cands_data = poll.questions_data[0]['answers']
    cands_count = len(cands_data)
    ballots_data = poll.result[0]
    candidates_dict = {candidate: 0 for candidate in cands_data}

    for ballot in ballots_data:
        if not ballot:
            continue
        ballot = to_absolute_answers(gamma_decode(ballot, cands_count, cands_count),
                                     cands_count)

        for i in ballot:
            candidates_dict[cands_data[i]] += Fraction(len(cands_data), len(ballot))

    candidate_data = [(candidate, votes) for candidate, votes in candidates_dict.items()]
    candidate_data.sort(key=lambda x: x[1], reverse=True)

    return candidate_data


