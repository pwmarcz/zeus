

from django.utils.translation import ugettext_lazy as _
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.conf import settings

from zeus.election_modules import ElectionModuleBase, election_module
from zeus.views.utils import set_menu

from helios.view_utils import render_template


@election_module
class PartiesListElection(ElectionModuleBase):

    module_id = 'parties'
    description = _('Party lists election')
    manage_questions_title = _('Manage ballot')
    messages = {
        'answer_title': _('Candidate'),
        'question_title': _('Party'),
    }
    auto_append_answer = True
    count_empty_question = True

    def questions_formset(self, extra):
        from zeus.forms import PartyForm
        return formset_factory(PartyForm, extra=extra,
                               can_delete=True, can_order=True)

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
            group = index
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
