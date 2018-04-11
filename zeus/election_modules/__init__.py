
import copy
import json
import os
import zipfile

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from zeus.reports import csv_from_polls, csv_from_score_polls,\
                         csv_from_stv_polls
from zeus.utils import get_filters, VOTER_TABLE_HEADERS, VOTER_SEARCH_FIELDS, \
    VOTER_BOOL_KEYS_MAP, VOTER_EXTRA_HEADERS


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
        raise NotImplemented

    def questions_update_view(self, request):
        raise NotImplemented

    def calculate_results(self, request):
        raise NotImplemented

    def get_booth_template(self, request):
        raise NotImplemented

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
        if lang:
            return os.path.join(RESULTS_PATH, '%s-%s-%s-results-%s.%s' %
                                (election, poll, name, lang, ext))
        else:
            return os.path.join(RESULTS_PATH, '%s-%s-%s-results.%s' %
                                (election, poll, name, ext))

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
        results_json = self.poll.zeus.get_results()
        with open(self.get_poll_result_file_path('json', 'json'), 'w') as f:
            json.dump(results_json, f)

    def generate_csv_file(self, lang):
        with open(self.get_poll_result_file_path('csv', 'csv', lang[0]), "w") as f:
            if self.module_id == "score":
                csv_from_score_polls(self.election, [self.poll], lang[0], f)
            elif self.module_id == "stv":
                csv_from_stv_polls(self.election, [self.poll], lang[0], f)
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
        results_name = self.election.name
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
from zeus.election_modules.unigovgr import * # noqa
