from __future__ import absolute_import
import datetime

from django.conf import settings
from django.test.client import Client
from django.contrib.auth.hashers import make_password

from helios.models import Election
from heliosauth.models import User, UserGroup
from zeus.models import Institution


class SetUpAdminAndClientMixin():
    def tearDown(self):
        self.institution.delete()

    def setUp(self):
        self.group = UserGroup.objects.create(name="ZEUS")
        self.institution = Institution.objects.create(name="test_inst")
        self.admin = User.objects.create(
            user_type="password",
            user_id="test_admin",
            info={"password": make_password("test_admin")},
            admin_p=True,
            institution=self.institution
            )
        self.admin.user_groups.add(self.group)
        self.locations = {
            'home': '/',
            'logout': '/auth/auth/logout',
            'login': '/auth/auth/login',
            'create': '/elections/new',
            'helpdesk': '/account_administration'
            }

        conf = settings.ZEUS_TESTS_ELECTION_PARAMS
        # set the voters number that will be produced for test
        self.voters_num = conf.get('NR_VOTERS', 2)
        # set the trustees number that will be produced for the test
        trustees_num = conf.get('NR_TRUSTEES', 2)
        trustees = "\n".join(",".join(['testName%x testSurname%x' % (x, x),
                   'test%x@mail.com' % x]) for x in range(0, trustees_num))
        # set the polls number that will be produced for the test
        self.polls_number = conf.get('NR_POLLS', 2)
        # set the number of max questions for simple election
        self.simple_election_max_questions_number =\
            conf.get('SIMPLE_MAX_NR_QUESTIONS', 2)
        # set the number of max answers for each question of simple election
        self.simple_election_max_answers_number =\
            conf.get('SIMPLE_MAX_NR_ANSWERS', 2)
        # set the number of max answers in score election
        self.score_election_max_answers =\
            conf.get('SCORE_MAX_NR_ANSWERS', 2)
        # set the number of max questions in party election
        self.party_election_max_questions_number =\
            conf.get('PARTY_MAX_NR_QUESTIONS', 2)
        # set the number of max answers in party election
        self.party_election_max_answers_number =\
            conf.get('PARTY_MAX_NR_ANSWERS', 2)
        # set the number of max candidates in stv election
        self.stv_election_max_answers_number =\
            conf.get('STV_MAX_NR_CANDIDATES', 2)

        start_date = datetime.datetime.now() + datetime.timedelta(hours=48)
        end_date = datetime.datetime.now() + datetime.timedelta(hours=56)

        self.election_form = {
            'trial': conf.get('trial', False),
            'name': 'test_election',
            'description': 'testing_election',
            'trustees': trustees,
            'voting_starts_at_0': start_date.strftime('%Y-%m-%d'),
            'voting_starts_at_1': start_date.strftime('%H:%M'),
            'voting_ends_at_0': end_date.strftime('%Y-%m-%d'),
            'voting_ends_at_1': end_date.strftime('%H:%M'),
            'help_email': 'test@test.com',
            'help_phone': 6988888888,
            'communication_language': conf.get('com_lang', 'en'),
            'official': None,
            'departments': 'Department of Test',
            'election_module': 'simple',
            }

        self.login_data = {'username': 'test_admin', 'password': 'test_admin'}
        self.c = Client()


def get_institution(**kwargs):
    '''
    Create, or retrieve an instituion. For testing purposes we only need one, so
    this instance is effectively a singleton.
    '''
    institution, _ = Institution.objects.get_or_create(**kwargs)
    return institution


def get_election(**kwargs):
    '''
    Create an election instance for testing. The field values can be customised
    using the names of the Election model, e.g.:
        - `name`: string
        - `voting_starts_at`: date string
        - `voting_ends_at`: date string
        - `trial`: boolean
    The only thing that cannot be modified is `institution`.
    etc.
    '''
    institution = get_institution()
    election, _ = Election.objects.get_or_create(institution=institution, **kwargs)
    return election


def get_messages_from_response(response):
    messages = []
    for item in response.context['messages']:
        messages.append(unicode(item))
    return messages
