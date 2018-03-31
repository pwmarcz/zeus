"""
Unit Tests for Auth Systems
"""


from .. import models

from django.db import IntegrityError

from django.test import TestCase

from django.core import mail

from ..auth_systems import AUTH_SYSTEMS

import pytest


class UserModelTests(TestCase):

    def setUp(self):
        pass

    def test_unique_users(self):
        """
        there should not be two users with the same user_type and user_id
        """
        for auth_system, auth_system_module in AUTH_SYSTEMS.items():
            models.User.objects.create(user_type=auth_system, user_id='foobar', info={'name': 'Foo Bar'})

            def double_insert():
                models.User.objects.create(user_type=auth_system, user_id='foobar', info={'name': 'Foo2 Bar'})

            with pytest.raises(IntegrityError):
                double_insert()

    def test_create_or_update(self):
        """
        shouldn't create two users, and should reset the password
        """
        for auth_system, auth_system_module in AUTH_SYSTEMS.items():
            u = models.User.update_or_create(user_type=auth_system, user_id='foobar_cou', info={'name': 'Foo Bar'})

            def double_update_or_create():
                new_name = 'Foo2 Bar'
                u2 = models.User.update_or_create(user_type=auth_system, user_id='foobar_cou', info={'name': new_name})

                assert u.id == u2.id
                assert u2.info['name'] == new_name

    def test_status_update(self):
        """
        check that a user set up with status update ability reports it as such,
        and otherwise does not report it
        """
        for auth_system, auth_system_module in AUTH_SYSTEMS.items():
            u = models.User.update_or_create(user_type=auth_system, user_id='foobar_status_update', info={'name': 'Foo Bar Status Update'})

            if hasattr(auth_system_module, 'send_message'):
                assert u.update_status_template is not None
            else:
                assert u.update_status_template is None

    def test_eligibility(self):
        """
        test that users are reported as eligible for something

        FIXME: also test constraints on eligibility
        """
        for auth_system, auth_system_module in AUTH_SYSTEMS.items():
            u = models.User.update_or_create(user_type=auth_system, user_id='foobar_status_update', info={'name': 'Foo Bar Status Update'})

            assert u.is_eligible_for({'auth_system': auth_system})

    def test_eq(self):
        for auth_system, auth_system_module in AUTH_SYSTEMS.items():
            u = models.User.update_or_create(user_type=auth_system, user_id='foobar_eq', info={'name': 'Foo Bar Status Update'})
            u2 = models.User.update_or_create(user_type=auth_system, user_id='foobar_eq', info={'name': 'Foo Bar Status Update'})

            assert u == u2

# FIXME: login CSRF should make these tests more complicated
# and should be tested for


class UserBlackboxTests(TestCase):

    def setUp(self):
        # create a bogus user
        self.test_user = models.User.objects.create(user_type='password', user_id='foobar-test@adida.net', name="Foobar User", info={'password': 'foobaz'})

    def test_email(self):
        """using the test email backend"""
        self.test_user.send_message("testing subject", "testing body")

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "testing subject"
        assert mail.outbox[0].to[0] == "Foobar User <foobar-test@adida.net>"
