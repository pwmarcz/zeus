
import copy
import json
import os
import zipfile

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from zeus.reports import csv_from_polls, csv_from_score_polls,\
                         csv_from_stv_polls, csv_from_sav_polls
from zeus.utils import get_filters, VOTER_TABLE_HEADERS, VOTER_SEARCH_FIELDS, \
    VOTER_BOOL_KEYS_MAP, VOTER_EXTRA_HEADERS
from zeus.views.utils import set_menu
from django.http import HttpResponseRedirect
from helios.view_utils import render_template


ELECTION_MODULES_CHOICES = []
MODULES_REGISTRY = {}


def election_module(cls):
    MODULES_REGISTRY[cls.module_id] = cls
    ELECTION_MODULES_CHOICES.append((cls.module_id, cls.description))
    return cls


def get_election_module(election):
    return MODULES_REGISTRY.get(election.election_module)(election)


def get_poll_module(poll):
    return MODULES_REGISTRY.get(poll.election.election_module)(poll.election,
                                                               poll)


class PollHooks(object):

    def __init__(self, module):
        self.module = module


class ElectionHooks(object):

    def __init__(self, module):
        self.module = module

    def post_create(self, election):
        pass


class ElectionModuleBase(ElectionHooks):

    module_id = None
    pdf_result = True
    csv_result = True
    json_result = True

    election_hooks_cls = ElectionHooks
    poll_hooks_cls = PollHooks
    display_poll_results = True
    election_results_partial = None

    max_questions_limit = None

    module_params = {}

    default_messages = {
        'description': _('Simple election with one or more questions'),
        'questions_title': _('Ballot'),
        'question_title': _('Question'),
        'answer_title': _('Answer'),
        'questions_view': 'helios.views.one_election_questions',
        'questions_empty_issue': _("Add questions to the election"),
        'max_limit_error': _("Too many choices"),
        'min_limit_error': _("Question '{0}' requires at least {1} choices."),
        'auto_append_answer': True,
        'count_empty_question': False
    }

    auto_append_answer = True
    count_empty_question = False

    def __init__(self, election, poll=None):
        self.logger = election.logger
        self.election = election
        self.poll = poll
        self.election_hooks = self.election_hooks_cls(self)
        self.poll_hooks = self.poll_hooks_cls(self)

        self._messages = copy.copy(self.default_messages)
        self._messages.update(self.messages)

    def __getattr__(self, name, *args, **kwargs):
        if name.endswith('_message'):
            msgkey = name.replace('_message', '')
            if msgkey in self._messages:
                return self._messages.get(msgkey)
        return super(ElectionModuleBase, self).__getattribute__(name, *args,
                                                                **kwargs)

    def questions_set(self):
        return self.poll.questions_count > 0

    def questions_list_view(self, request):
        raise NotImplementedError

    def questions_update_view(self, request, election, poll):
        from zeus.utils import poll_reverse
        from zeus.forms import DEFAULT_ANSWERS_COUNT, \
                MAX_QUESTIONS_LIMIT

        extra = 1
        if poll.questions_data:
            extra = 0

        questions_formset = self.questions_formset(extra)
        if request.method == 'POST':
            formset = questions_formset(request.POST, request.FILES, initial=poll.questions_data)
            should_submit = not request.FILES and formset.is_valid()
            if should_submit:
                cleaned_data = formset.cleaned_data
                questions_data = self.extract_question_data(cleaned_data)

                poll.questions_data = questions_data
                poll.update_answers()
                poll.logger.info("Poll ballot updated")
                self.update_poll_params(poll, formset.cleaned_data)
                poll.save()

                url = poll_reverse(poll, 'questions')
                return HttpResponseRedirect(url)
        else:
            formset = questions_formset(initial=poll.questions_data)

        context = {
            'default_answers_count': DEFAULT_ANSWERS_COUNT,
            'formset': formset,
            'max_questions_limit': self.max_questions_limit or MAX_QUESTIONS_LIMIT,
            'election': election,
            'poll': poll,
            'module': self
        }
        set_menu('questions', context)
        tpl = f'election_modules/{self.module_id}/election_poll_questions_manage'
        return render_template(request, tpl, context)

    def update_poll_params(self, poll, cleaned_data):
        pass

    def questions_formset(self, extra):
        raise NotImplementedError

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

    def calculate_results(self, request):
        raise NotImplementedError

    def get_booth_template(self, request):
        raise NotImplementedError

    @property
    def params(self):
        data = dict()
        data.update(self._messages)
        data.update({
            'auto_append_answer': self.auto_append_answer,
            'count_empty_question': self.count_empty_question
        })
        if self.module_params:
            data.update(self.module_params)
        return data

    def get_poll_result_file_path(self, name, ext, lang=None):
        RESULTS_PATH = getattr(settings, 'ZEUS_RESULTS_PATH',
            os.path.join(settings.MEDIA_ROOT, 'results'))
        election = self.election.short_name
        poll = self.poll.short_name

        short_name = '%s-%s' % (election, poll)
        # Work around 'File name too long'
        # (the usual limit is 255 bytes for ext fs)
        short_name = short_name[:160]

        if lang:
            return os.path.join(RESULTS_PATH, '%s-%s-results-%s.%s' %
                                (short_name, name, lang, ext))
        else:
            return os.path.join(RESULTS_PATH, '%s-%s-results.%s' %
                                (short_name, name, ext))

    def get_election_result_file_path(self, name, ext, lang=None):
        RESULTS_PATH = getattr(settings, 'ZEUS_RESULTS_PATH',
            os.path.join(settings.MEDIA_ROOT, 'results'))
        election = self.election.short_name
        if lang:
            return os.path.join(RESULTS_PATH, '%s-%s-results-%s.%s' %
                                (election, name, lang, ext))
        else:
            return os.path.join(RESULTS_PATH, '%s-%s-results.%s' %
                                (election, name, ext))

    def generate_json_file(self):
        if self.module_id != "sav":
            results_json = self.poll.zeus.get_results()
        else:
            results = count_sav_results_for_poll(self.poll)
            results_json = {
                candidate: {
                    "float_votes": float(votes),
                    "fraction_numerator": votes.numerator,
                    "fraction_denominator": votes.denominator,
                }
                for candidate, votes in results
            }

        with open(self.get_poll_result_file_path('json', 'json'), 'w') as f:
            json.dump(results_json, f)

    def generate_csv_file(self, lang):
        with open(self.get_poll_result_file_path('csv', 'csv', lang[0]), "w") as f:
            if self.module_id == "score":
                csv_from_score_polls(self.election, [self.poll], lang[0], f)
            elif self.module_id == "stv":
                csv_from_stv_polls(self.election, [self.poll], lang[0], f)
            elif self.module_id == "sav":
                csv_from_sav_polls(self.election, [self.poll], lang[0], f)
            else:
                csv_from_polls(self.election, [self.poll], lang[0], f)

    def generate_election_csv_file(self, lang):
        with open(self.get_election_result_file_path('csv', 'csv', lang[0]), "w") as f:
            if self.module_id == "score":
                csv_from_score_polls(self.election, self.election.polls.all(),
                    lang[0], f)
            elif self.module_id == "stv":
                csv_from_stv_polls(self.election, self.election.polls.all(),
                                   lang[0], f)
            elif self.module_id == "sav":
                csv_from_sav_polls(self.election, self.election.polls.all(),
                                   lang[0], f)
            else:
                csv_from_polls(self.election, self.election.polls.all(),
                               lang[0], f)

    def generate_election_zip_file(self, lang):
        zippath = self.get_election_result_file_path('zip', 'zip', lang[0])
        all_docs_zip = zipfile.ZipFile(zippath, 'w')

        election_csvpath = self.get_election_result_file_path('csv', 'csv',
                                                              lang[0])
        if not os.path.exists(election_csvpath):
            self.generate_electon_csv_file(lang)
        basename = os.path.basename(election_csvpath)
        all_docs_zip.write(election_csvpath, basename)
        election_pdfpath = self.get_election_result_file_path('pdf', 'pdf',
                                                                lang[0])
        if not os.path.exists(election_pdfpath):
            self.module.generate_election_result_docs(lang)
        basename = os.path.basename(election_pdfpath)
        all_docs_zip.write(election_pdfpath, basename)

        poll_docpaths = []
        for poll in self.election.polls.all():
            module = poll.get_module()
            poll_csvpath = module.get_poll_result_file_path('csv', 'csv', lang[0])
            poll_docpaths.append(poll_csvpath)
            if not os.path.exists(poll_csvpath):
                module.generate_csv_file(lang)
            poll_jsonpath = module.get_poll_result_file_path('json', 'json')
            poll_docpaths.append(poll_jsonpath)
            if not os.path.exists(poll_jsonpath):
                module.generate_json_file()
            poll_docpaths.append(poll_jsonpath)
            poll_pdfpath = module.get_poll_result_file_path('pdf', 'pdf', lang[0])
            poll_docpaths.append(poll_pdfpath)
            if not os.path.exists(poll_pdfpath):
                module.generate_result_docs(lang)
        poll_docpaths = set(poll_docpaths)
        for path in poll_docpaths:
            basename = os.path.basename(path)
            all_docs_zip.write(path, basename)

        all_docs_zip.close()

    def generate_result_docs(self, lang):
        from zeus.results_report import build_doc
        score = self.election.election_module == "score"
        parties = self.election.election_module == "parties"
        poll = self.poll
        build_doc(_('Results'), self.election.name,
                      self.election.institution.name,
                      self.election.voting_starts_at, self.election.voting_ends_at,
                      self.election.voting_extended_until,
                      [(poll.name,
                        poll.zeus.get_results(),
                        poll.questions_data,
                        poll.questions[0]['answers'],
                        poll.voters.all())],
                      lang,
                      self.get_poll_result_file_path('pdf', 'pdf', lang[0]),
                      score=score, parties=parties)

    def generate_election_result_docs(self, lang):
        from zeus.results_report import build_doc
        pdfpath = self.get_election_result_file_path('pdf', 'pdf', lang[0])
        polls_data = []
        score = self.election.election_module == "score"
        parties = self.election.election_module == "parties"

        for poll in self.election.polls.filter():
            polls_data.append((poll.name,
                               poll.zeus.get_results(),
                               poll.questions_data,
                               poll.questions[0]['answers'],
                               poll.voters.all()))

        build_doc(_('Results'), self.election.name, self.election.institution.name,
                self.election.voting_starts_at, self.election.voting_ends_at,
                self.election.voting_extended_until,
                polls_data,
                lang,
                pdfpath, score=score, parties=parties)

    def run_hook(self, name, *args, **kwargs):
        if self.poll:
            args = [self.poll] + list(args)
            hooks = self.poll_hooks
        else:
            args = [self.election] + list(args)
            hooks = self.election_hooks

        hook = getattr(hooks, name, None)
        if hook and callable(hook):
            self.logger.debug("Run %s hook for %s", name, self.module_id)
            return hook(*args, **kwargs)

        self.logger.info("Missing %s hook for %s", name, self.module_id)

    def get_voters_list_headers(self, request=None):
        return VOTER_TABLE_HEADERS

    def get_voters_search_fields(self, request=None):
        return VOTER_SEARCH_FIELDS

    def get_voters_bool_keys_map(self, request=None):
        return VOTER_BOOL_KEYS_MAP

    def get_voters_extra_headers(self, request=None):
        return VOTER_EXTRA_HEADERS

    def filter_voters(self, voters, q_param, request=None):
        headers = self.get_voters_list_headers(request)
        search = self.get_voters_search_fields(request)
        bool_keys = self.get_voters_bool_keys_map(request)
        extra = self.get_voters_extra_headers(request)
        filters = get_filters(q_param, headers, search, bool_keys, extra)
        return voters.filter(filters)

    def can_delete_poll_voters(self):
        return True

    def can_edit_polls(self):
        return True


# TODO change to explicit imports
from zeus.election_modules.simple import *  # noqa
from zeus.election_modules.parties import * # noqa
from zeus.election_modules.score import * # noqa
from zeus.election_modules.stv import * # noqa
from zeus.election_modules.sav import * # noqa
from zeus.election_modules.unigovgr import * # noqa
