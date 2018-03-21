from __future__ import print_function

import datetime

from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse

from helios.models import Election
from zeus.tests.utils import SetUpAdminAndClientMixin


def today_plus_days(days):
    return datetime.date.today() + datetime.timedelta(days=days)


class TestHomeView(SetUpAdminAndClientMixin, TestCase):
    def setUp(self):
        super(TestHomeView, self).setUp()

    def login(self):
        self.c.post(self.locations['login'], self.login_data)

    def create_election(self, **kwargs):
        '''
        Create an election instance for testing. The fields can be customised
        using the following kwargs:
            - name: string
            - voting_starts_at_0: date string
            - voting_ends_at_0: date string
            - trial: boolean
        '''
        self.election_form['departments'] = 'test_departments'
        self.election_form['election_module'] = 'simple'

        # create a copy of the form and customize it sing the provided params
        form = dict(self.election_form)
        for param, value in kwargs.items():
            form[param] = value
        self.c.post(self.locations['create'], form, follow=True)

        return Election.objects.all().latest('created_at')

    def post_and_get_response(self):
        """
        Create an election and post on admin_home
        to change their official status.
        """
        election = self.create_election()
        return self.c.post(
            reverse('admin_home'),
            {
                'official': [1],
                'uuid': [election.uuid]
            }
        )

    def test_post_without_login(self):
        """
        If someone tries to do a POST request on admin_home
        without having logged in the view should respond
        with a 403(Permission Denied) HTTP code.
        """
        response = self.c.post(
            reverse('admin_home'),
            {}
        )

        assert response.status_code == 403

    def test_post_without_superadmin(self):
        """
        If someone tries to do a POST request on admin_home
        without having superadmin access the view should
        respond with a 403(Permission Denied) HTTP code.
        """
        self.login()

        response = self.post_and_get_response()

        assert response.status_code == 403

    def test_post_with_superadmin(self):
        """
        If someone tries to do a POST request on admin_home
        with superadmin access the view should
        respond with a 302(Redirection) HTTP code.
        """
        self.admin.superadmin_p = True
        self.admin.save()

        self.login()

        response = self.post_and_get_response()

        assert response.status_code == 302

    def test_get_without_superadmin(self):
        """
        If someone does a GET request on admin_home
        without superadmin access the template
        returned should not contain a form.
        """
        self.login()
        election = self.create_election()

        response = self.c.get(
            reverse('admin_home'),
            {}
        )

        self.assertNotContains(response, '<select name="official">')

    def test_get_with_superadmin(self):
        """
        If someone does a GET request on admin_home
        with superadmin access the template
        returned should contain a form.
        """
        self.admin.superadmin_p = True
        self.admin.save()

        self.login()

        # when there are no elections created, we should get a redirect
        response = self.c.get(reverse('admin_home'), {})
        self.assertEqual(response.status_code, 302)

        election = self.create_election(name='first_election')

        response = self.c.get(
            reverse('admin_home'),
            {}
        )

        self.assertContains(response, '</form>')
        self.assertContains(response, '<select name="official">')
        self.assertContains(response, '<input type="submit"')
        self.assertContains(response, '<input type="hidden"')

        # ensure the ordering works
        newer_newer = self.create_election(name='second_election')

        response = self.c.get(reverse('admin_home'), {'order': 'name', 'order_type': 'desc'})
        self.assertEqual(response.context['elections_administered'][0].name, 'second_election')
        self.assertEqual(response.context['elections_administered'][1].name, 'first_election')

        response = self.c.get(reverse('admin_home'), {'order': 'created_at', 'order_type': 'asc'})
        self.assertEqual(response.context['elections_administered'][0].name, 'first_election')
        self.assertEqual(response.context['elections_administered'][1].name, 'second_election')

        # when the order param is invalid, should sort by name, descending
        response = self.c.get(reverse('admin_home'), {'order': 'boom'})
        self.assertEqual(response.context['elections_administered'][0].name, 'second_election')
        self.assertEqual(response.context['elections_administered'][1].name, 'first_election')

        # ensure elections_per_page is handled right
        response = self.c.get(reverse('admin_home'), {'limit': 1})
        self.assertEqual(response.context['elections_per_page'], 1)

        response = self.c.get(reverse('admin_home'), {'limit': '1'})
        self.assertEqual(response.context['elections_per_page'], 1)

        # when limit is invalid, it should fall back to the default
        response = self.c.get(reverse('admin_home'), {'limit': 'boom'})
        self.assertEqual(response.context['elections_per_page'], 20)

    def test_find_elections(self):
        from zeus.views.admin import find_elections

        self.admin.superadmin_p = True
        self.admin.save()
        self.login()

        election_a = self.create_election(
            name='election A',
            voting_starts_at_0=today_plus_days(days=1).strftime('%Y-%m-%d'),
            voting_ends_at_0=today_plus_days(days=2).strftime('%Y-%m-%d')
        )
        election_b = self.create_election(
            name='election B',
            voting_starts_at_0=today_plus_days(days=4).strftime('%Y-%m-%d'),
            voting_ends_at_0=today_plus_days(days=5).strftime('%Y-%m-%d')
        )
        election_c = self.create_election(
            name='election C',
            trial=True
        )
        election_a
        for i, e in enumerate([election_a, election_b, election_c]):
            e.completed_at = today_plus_days(days=6+i)
            e.save()

        # in the default case elections should be sorted by created_at, desc
        request = RequestFactory().get(reverse('elections_report_csv'), {})
        request.user = self.admin
        elections = find_elections(request)
        assert len(elections) == 2
        assert elections[0] == election_b
        assert elections[1] == election_a

        request = RequestFactory().get(reverse('elections_report_csv'), {
            'order': 'name',
            'order_type': 'asc',
        })
        request.user = self.admin
        elections = find_elections(request)
        assert len(elections) == 2
        assert elections[0] == election_a
        assert elections[1] == election_b

        request = RequestFactory().get(reverse('elections_report_csv'), {
            'start_date': today_plus_days(days=3).strftime('%d %b %Y'),
        })
        request.user = self.admin
        elections = find_elections(request)
        assert len(elections) == 1
        assert elections[0] == election_b

        request = RequestFactory().get(reverse('elections_report_csv'), {
            'end_date': today_plus_days(days=3).strftime('%d %b %Y'),
        })
        request.user = self.admin
        elections = find_elections(request)
        assert len(elections) == 1
        assert elections[0] == election_a

