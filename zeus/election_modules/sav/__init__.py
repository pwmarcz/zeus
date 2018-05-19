from django.utils.translation import ugettext_lazy as _
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.conf import settings

from zeus.election_modules import ElectionModuleBase, election_module
from zeus.views.utils import set_menu

from helios.view_utils import render_template


@election_module
class SavElection(ElectionModuleBase):
    module_id = 'sav'
    description = _('Satisfaction approval voting')
    messages = {
        'answer_title': _('Candidate'),
        'question_title': _('Candidates List')
    }
    auto_append_answer = True
    count_empty_question = False
    booth_questions_tpl = 'question_counting'
    no_questions_added_message = _('No questions set')
    manage_questions_title = _('Manage questions')
    module_params = {
        'ranked': True
    }

    results_template = "election_modules/sav/results.html"

    pdf_result = True
    csv_result = True
    json_result = True

