
from django.test import TestCase

import datetime
import os

from helios.models import Election, Poll, Voter
from heliosauth.models import User
from zeus.models import Institution
from zeus.tests.utils import SetUpAdminAndClientMixin


class TestPollViews(SetUpAdminAndClientMixin, TestCase):

    def setUp(self):
        super(TestPollViews, self).setUp()

        self.c.post(self.locations['login'], self.login_data)
        self.institution = self.get_institution()
        self.election = Election.objects.create(name="election", voting_starts_at=datetime.date.today(),
                                     voting_ends_at=datetime.date.today() + datetime.timedelta(days=1),
                                     trial=True, institution=self.institution)
        user = User.objects.get()
        self.election.admins.add(user)
        self.election.save()

    def get_institution(self, **kwargs):
        '''
        Create, or retrieve an instituion. For testing purposes we only need one, so
        this instance is effectively a singleton.
        '''
        institution, _ = Institution.objects.get_or_create(**kwargs)
        return institution

    def create_poll(self, election, **kwargs):
        self.c.post(self.locations['login'], self.login_data)
        poll, _ = Poll.objects.get_or_create(election=election, **kwargs)
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
            with open(fname, "w") as fp:
                for i in range(1, self.voters_num + 1):
                    voter = "%s,voter%s@mail.com,test_name%s,test_surname%s\n" \
                            % (i, i, i, i)
                    fp.write(voter)
            counter += 1
        return voter_files

    def submit_voters_file(self):
        voter_files = self.get_voters_file()
        for p_uuid in self.p_uuids:
            upload_voters_location = '/elections/%s/polls/%s/voters/upload' \
                                     % (self.e_uuid, p_uuid)
            with open(voter_files[p_uuid]) as f:
                self.c.post(
                    upload_voters_location,
                    {'voters_file': f,
                     'encoding': 'iso-8859-7'}
                )
            self.c.post(upload_voters_location, {'confirm_p': 1, 'encoding': 'iso-8859-7'})

    def voter_login(self, voter, voter_login_url=None):
        r = self.c.get(voter_login_url, follow=True)
        assert r.status_code == 200

    def test_poll_questions(self):
        poll = self.create_poll(election=self.election, name="poll")

        response = self.c.get('/elections/{}/polls/{}/questions'.format(self.election.uuid, poll.uuid))
        assert response.status_code == 302
        self.assertRedirects(response, '/elections/{}/polls/{}/questions/manage'.format(self.election.uuid, poll.uuid),
                             fetch_redirect_response=True)

        self.e_uuid = self.election.uuid
        self.submit_voters_file()
        voter = Voter.objects.all()[0]
        url = voter.get_quick_login_url()

        self.c.post(self.locations['logout'])

        self.voter_login(voter, url)
        response = self.c.get('/elections/{}/polls/{}/questions'.format(self.election.uuid, poll.uuid))

        assert response.status_code == 200
        module = poll.get_module()
        tpl = getattr(module, 'questions_list_template', 'election_poll_questions')

        self.assertTemplateUsed(response, tpl + '.html')

    def test_poll_add_batch_file(self):
        self.election.linked_polls = True
        self.election.save()
        self.e_uuid = self.election.uuid
        self.create_poll(self.election, name="linked_poll")
        poll = Poll.objects.all()[0]

        with open(os.path.join(os.path.dirname(__file__),
                               'test_sample_survey_for_linked_election.yml')) as batch_file:
            response = self.c.post('/elections/{}/polls/add'.format(self.election.uuid),
                                   {
                                       'batch_file': batch_file,
                                   })

        assert response.status_code == 302
        self.assertRedirects(response, '/elections/{}/polls/'.format(self.election.uuid))

        polls = list(Poll.objects.order_by('id'))
        assert len(polls) == 4
        assert len(polls[0].questions[0]['answers']) == 52
        assert len(polls[1].questions[0]['answers']) == 13
        assert len(polls[2].questions[0]['answers']) == 13
        assert len(polls[3].questions[0]['answers']) == 17

    def test_poll_remove(self):
        self.e_uuid = self.election.uuid
        self.create_poll(self.election, name="poll")
        poll = Poll.objects.all()[0]
        response = self.c.post('/elections/{}/polls/{}/remove'.format(self.election.uuid, poll.uuid))

        assert response.status_code == 302
        assert not Poll.objects.filter(name="poll").exists()
        self.assertRedirects(response, '/elections/{}/polls/'.format(self.election.uuid))
