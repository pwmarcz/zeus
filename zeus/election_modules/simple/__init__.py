

from django.utils.translation import gettext_lazy as _
from django.forms.formsets import formset_factory
from django.conf import settings

from zeus.election_modules import ElectionModuleBase, election_module


@election_module
class SimpleElection(ElectionModuleBase):

    module_id = 'simple'
    description = _('Simple election with one or more questions')
    messages = {}
    auto_append_answer = True
    count_empty_question = False
    booth_questions_tpl = ''
    no_questions_added_message = _('No questions set')
    manage_questions_title = _('Manage questions')

    def questions_formset(self, extra=1):
        from zeus.forms import QuestionForm
        return formset_factory(QuestionForm, extra=extra,
                               can_delete=True, can_order=True)

    def update_answers(self):
        answers = []
        questions_data = self.poll.questions_data or []
        prepend_empty_answer = True

        if self.auto_append_answer:
            prepend_empty_answer = True

        for index, q in enumerate(questions_data):
            question = q['question'].replace(":", "{semi}") \
                                    .replace("\r\n", "{newline}") \
                                    .replace("\n", "{newline}")
            q_answers = ["%s: %s" % (question, ans) for ans in
                         q['answers']]
            group = 0
            if prepend_empty_answer:
                params_max = int(q['max_answers'])
                params_min = int(q['min_answers'])
                if self.count_empty_question:
                    params_min = 0
                params = "%d-%d, %d" % (params_min, params_max, group)
                q_answers.insert(0, "%s: %s" % (question, params))
            answers = answers + q_answers
        self.poll._init_questions(len(answers))
        self.poll.questions[0]['answers'] = answers

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

    def get_booth_template(self, request):
        raise NotImplementedError
