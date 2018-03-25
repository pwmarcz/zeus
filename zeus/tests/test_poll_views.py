from django.test import TestCase

import datetime
import os

from helios.models import Election, Poll, Voter
from heliosauth.models import User
from zeus.models import Institution
from zeus.tests.utils import SetUpAdminAndClientMixin


class TestElectionBase(SetUpAdminAndClientMixin, TestCase):

    def setUp(self):
        super(TestElectionBase, self).setUp()
        self.local_verbose = os.environ.get('ZEUS_TESTS_VERBOSE', None)
        self.celebration = (
            " _________ ___  __\n"
            "|\   __  \|\  \|\  \\\n"
            "\ \  \ \  \ \  \/  /_\n"
            " \ \  \ \  \ \   ___ \\\n"
            "  \ \  \_\  \ \  \\\ \ \\ \n"
            "   \ \_______\ \__\\\ \_\\\n"
            "    \|_______|\|__| \|_|\n"
            )

    def verbose(self, message):
        if self.local_verbose:
            print message


    def get_institution(self, **kwargs):
        '''
        Create, or retrieve an instituion. For testing purposes we only need one, so
        this instance is effectively a singleton.
        '''
        institution, _ = Institution.objects.get_or_create(**kwargs)
        return institution

    def get_election(self, **kwargs):
        self.c.post(self.locations['login'], self.login_data)
        institution = self.get_institution()
        election, _ = Election.objects.get_or_create(institution=institution, **kwargs)
        return election

    def get_messages_from_response(self, response):
        messages = []
        for item in response.context['messages']:
            messages.append(unicode(item))
        return messages

    def create_poll(self, **kwargs):
        election = self.get_election(name="election", voting_starts_at=datetime.date.today(),
                                     voting_ends_at=datetime.date.today() + datetime.timedelta(days=1),
                                     trial=True)
        self.c.post(self.locations['login'], self.login_data)
        poll, _ = Poll.objects.get_or_create(**kwargs)
        self.p_uuids = []
        for poll in election.polls.all():
            self.p_uuids.append(poll.uuid)
        return poll

    def get_voters_file(self):
        counter = 0
        voter_files = {}
        for p_uuid in self.p_uuids:
            fname = '/tmp/random_voters%s.csv' % counter
            voter_files[p_uuid] = fname
            fp = file(fname, 'w')
            for i in range(1, self.voters_num+1):
                voter = "%s,voter%s@mail.com,test_name%s,test_surname%s\n" \
                    % (i, i, i, i)
                fp.write(voter)
            fp.close()
            counter += 1
        self.verbose('+ Voters file created')
        return voter_files

    def submit_voters_file(self):
        voter_files = self.get_voters_file()
        for p_uuid in self.p_uuids:
            upload_voters_location = '/elections/%s/polls/%s/voters/upload' \
                % (self.e_uuid, p_uuid)
            self.c.post(
                upload_voters_location,
                {'voters_file': file(voter_files[p_uuid]),
                 'encoding': 'iso-8859-7'}
                )
            self.c.post(upload_voters_location, {'confirm_p': 1, 'encoding': 'iso-8859-7'})
        self.verbose('+ Voters file submitted')

    def voter_login(self, voter, voter_login_url=None):
        r = self.c.get(voter_login_url, follow=True)
        assert r.status_code == 200


class TestPollViews(TestElectionBase):

    def test_poll_questions(self):
        self.c.post(self.locations['login'], self.login_data)
        election = self.get_election(name="election", voting_starts_at=datetime.date.today(),
                                     voting_ends_at=datetime.date.today() + datetime.timedelta(days=1),
                                     trial=True)
        user = User.objects.get()
        election.admins.add(user)
        poll = self.create_poll(election=election, name="poll")

        response = self.c.get('/elections/{}/polls/{}/questions'.format(election.uuid, poll.uuid))
        assert response.status_code == 302
        self.assertRedirects(response, '/elections/{}/polls/{}/questions/manage'.format(election.uuid, poll.uuid),
                             fetch_redirect_response=True)

        self.e_uuid = election.uuid
        self.submit_voters_file()
        voter = Voter.objects.all()[0]
        url = voter.get_quick_login_url()

        self.c.post(self.locations['logout'])

        self.voter_login(voter, url)
        response = self.c.get('/elections/{}/polls/{}/questions'.format(election.uuid, poll.uuid))

        assert response.status_code == 200
        module = poll.get_module()
        tpl = getattr(module, 'questions_list_template', 'election_poll_questions')

        self.assertTemplateUsed(response, tpl + '.html')


