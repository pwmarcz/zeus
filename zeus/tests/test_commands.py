from django.test import TestCase
from django.core.management import call_command
import mock

from heliosauth.models import User, UserGroup
from zeus.models import Institution


class CreateUserTest(TestCase):

    @mock.patch('heliosauth.management.commands.manage_users.getpass.getpass')
    def test_create_user(self, getpass):
        getpass.return_value = 'password'
        institution = Institution.objects.create(name="razem")
        call_command('manage_users', "kotek", create_user=True, institution=institution.id)
        user = User.objects.get(user_id="kotek")
        assert user.user_groups.all()[0] == UserGroup.objects.get(name='default')

