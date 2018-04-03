
from six.moves.urllib.parse import urlencode

from django.test import TestCase
from django.urls import reverse
from helios.models import Election
from zeus.forms import ElectionForm
from zeus.tests.utils import (
    SetUpAdminAndClientMixin,
    get_election,
    get_poll,
    get_trustee,
    get_voter,
)


class TestAddOrUpdateElection(SetUpAdminAndClientMixin, TestCase):
    def setUp(self):
        super(TestAddOrUpdateElection, self).setUp()

    def test_election_create(self):
        # election-create form cannot be seen without logging in
        response = self.c.get(reverse('election_create'), {})
        assert response.status_code == 403

        # and posting the data also shouldn't work
        response = self.c.post(
            reverse('election_create'),
            urlencode(self.election_form),
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 403

        # but should be visible for logged-in users
        self.login()
        response = self.c.get(reverse('election_create'), {})
        assert response.status_code == 200
        assert isinstance(response.context['election_form'], ElectionForm)
        assert response.context['election'] is None

        # and posting the form should create a new Election
        assert Election.objects.count() == 0
        response = self.c.post(
            reverse('election_create'),
            urlencode(self.election_form),
            content_type='application/x-www-form-urlencoded'
        )
        # success means a redirect and an election created
        assert response.status_code == 302
        assert Election.objects.count() == 1

    def test_election_edit(self):
        # editing elections should only be available to logged-in users
        election = get_election(name='election A')
        response = self.c.get(reverse('election_edit', kwargs={'election_uuid': election.uuid}))
        assert response.status_code == 403

        response = self.c.post(reverse('election_edit', kwargs={'election_uuid': election.uuid}))
        assert response.status_code == 403

        # but only those, who have the permission to edit this election
        self.login()
        response = self.c.post(reverse('election_edit', kwargs={'election_uuid': election.uuid}))
        assert response.status_code == 403

        # the happy case: logged-in user with permissions
        election.admins.add(self.admin)

        # should see the form with the correct election details in case of GET
        response = self.c.get(reverse('election_edit', kwargs={'election_uuid': election.uuid}))
        assert response.status_code == 200
        assert isinstance(response.context['election_form'], ElectionForm)
        assert response.context['election'] == election

        # and should be able to modify it using POST
        new_form = dict(self.election_form)
        new_form['name'] = 'election B'
        data = urlencode(new_form)
        response = self.c.post(
            reverse('election_edit', kwargs={'election_uuid': election.uuid}),
            data,
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 302
        election.refresh_from_db()
        assert election.name == 'election B'


class TestTrusteesList(SetUpAdminAndClientMixin, TestCase):
    def setUp(self):
        super(TestTrusteesList, self).setUp()

    # def test_trustee_list_get(self):
    #     election = get_election()
    #     trustee = get_trustee(election=election)
    #     poll = get_poll(election=election)
    #     voter = get_voter(poll=poll)

    #     self.login()
    #     election.admins.add(self.admin)

    #     response = self.c.get(
    #         reverse('election_trustees_list', kwargs={'election_uuid': election.uuid}),
    #         {'voter': voter}
    #     )
    #     assert response.context['election'] == election
    #     assert trustee in response.context['trustees']
    #     # assert response.context['poll'] == poll
    #     assert response.context['voter'] == voter
