
from itertools import zip_longest

from django.utils.translation import ugettext_lazy as _
from django.forms.formsets import formset_factory
from django.conf import settings

from zeus.election_modules import ElectionModuleBase, election_module


@election_module
class ScoreBallotElection(ElectionModuleBase):

    module_id = 'score'
    description = _('Score voting election')
    messages = {}
    auto_append_answer = True
    count_empty_question = False
    results_template = "election_modules/score/results.html"
    manage_questions_title = _('Manage questions')
    csv_result = True
    pdf_result = True

    max_questions_limit = 1

    module_params = {}

    messages = {}

    def questions_formset(self, extra):
        from zeus.forms import ScoresForm, RequiredFormset
        return formset_factory(ScoresForm,
                               formset=RequiredFormset,
                               extra=extra,
                               can_delete=True,
                               can_order=True)

    def update_answers(self):
        answers = []
        scores = []
        questions_data = self.poll.questions_data or []

        for index, q in enumerate(questions_data):
            question = q['question'].replace(":", "{semi}") \
                                    .replace("\r\n", "{newline}") \
                                    .replace("\n", "{newline}")
            q_answers = []

            for answer in q['answers']:
                q_answers.append("%s: %s" % (question, answer))
            scores += [str(100 * index+int(x)) for x in q['scores']]
            answers = answers + q_answers

        qdata = questions_data[0]
        min, max = int(qdata['min_answers']), \
            int(qdata['max_answers'])
        params = "%d-%d" % (min, max)
        answers.append("%s" % (params, ))

        poll_answers = []
        scores = reversed(scores)
        for answer, score in zip_longest(answers[:-1], scores):
            if answer is not None:
                poll_answers.append(answer)
            if score is not None:
                poll_answers.append(score)

        poll_answers.append(answers[-1])

        self.poll._init_questions(len(poll_answers))
        self.poll.questions[0]['answers'] = poll_answers

        # save index references
        for index, q in enumerate(self.poll.questions_data):
            question = q['question'].replace(":", "{semi}") \
                                    .replace("\r\n", "{newline}") \
                                    .replace("\n", "{newline}")
            q['answer_indexes'] = {}
            q['score_indexes'] = {}
            for answer in q['answers']:
                q['answer_indexes'][answer] = poll_answers.index("%s: %s" % (question, answer))
            for score in q['scores']:
                q['score_indexes'][score] = poll_answers.index(str(100 * index+int(score)))

    def calculate_results(self, request):
        raise NotImplementedError

    def get_booth_template(self, request):
        raise NotImplementedError

    def compute_results(self):
        self.generate_json_file()
        for lang in settings.LANGUAGES:
            self.generate_csv_file(lang)
            self.generate_result_docs(lang)

    def compute_election_results(self):
        for lang in settings.LANGUAGES:
            self.generate_election_csv_file(lang)
            self.generate_election_result_docs(lang)
            self.generate_election_zip_file(lang)
