import sys

from django.core.management.base import BaseCommand

from heliosauth.models import User, UserGroup, SMSBackendData
from django.contrib.auth.hashers import make_password
from zeus.models import Institution

import getpass

class Command(BaseCommand):
    args = '<username>'
    help = 'Create a non ecounting elections admin user'

    def add_arguments(self, parser):
        parser.add_argument('param', nargs='?')
        parser.add_argument('--name',
                           action='store',
                           dest='name',
                           default=None,
                           help='Full user name')
        parser.add_argument('--superuser',
                           action='store_true',
                           dest='superuser',
                           default=False,
                           help='Give superuser permissions to user')
        parser.add_argument('--manager',
                            action='store_true',
                            dest='manager',
                            default=False,
                            help='Give manager permissions to user')
        parser.add_argument('--institution',
                           action='store',
                           dest='institution',
                           default=None,
                           help='Institution id (used in --create-user)')
        parser.add_argument('--create-institution',
                           action='store_true',
                           dest='create_institution',
                           default=False,
                           help='Institution id')
        parser.add_argument('--create-user',
                           action='store_true',
                           dest='create_user',
                           default=False,
                           help='Create a new user')
        parser.add_argument('--remove-user',
                           action='store_true',
                           dest='remove_user',
                           default=False,
                           help='Remove an existing user')
        parser.add_argument('--reset-password',
                           action='store_true',
                           dest='reset_password',
                           default=False,
                           help='Reset a user\'s password')
        parser.add_argument('--enable-sms',
                           action='store',
                           dest='enable_sms',
                           default=False,
                           help='enable user sms backend. Provide sender id as value to this argument.')
        parser.add_argument('--sms-limit',
                           action='store',
                           dest='sms_limit',
                           default=False,
                           help='update sms limit for user')

    def get_user(self, pk_or_userid):
        pk_or_userid = pk_or_userid.strip()

        pk = None
        userid = None
        try:
            pk = int(pk_or_userid)
        except ValueError:
            userid = pk_or_userid

        if pk:
            return User.objects.get(pk=pk)
        return User.objects.get(user_id=userid)

    def handle(self, **options):
        reload(sys)
        sys.setdefaultencoding('utf-8')

        if options.get('create_institution'):
            if not options['param']:
                print "Provide the institution name"
                exit()

            name = options['param'].strip()
            Institution.objects.create(name=options['param'].strip())

        if options.get('remove_user'):
            if not options['param']:
                print "Provide a user id"
                exit()

            user = User.objects.get(pk=int(options['param'].strip()))
            print "User has %d elections objects which will be removed" % user.elections.count()
            confirm = raw_input('Write "yes of course" if you are sure you want to remove \'%s\' ? ' % user.user_id)
            if confirm == "yes of course":
                user.delete()
            else:
                exit()
            print "User removed"

        if options.get("reset_password"):
            if not options['param']:
                print "Provide a user id and a password"
                exit()
            user = self.get_user(options['param'])
            password = getpass.getpass("Password:")
            password_confirm = getpass.getpass("Confirm password:")
            user.info['password'] = make_password(password)
            user.save()

        if options.get("enable_sms"):
            if not options['param']:
                print "Provide a user id and sms backend sender id"
                exit()

            sender = options.get('enable_sms', 'ZEUS')
            creds = getpass.getpass("Credentials (e.g. username:pass):")
            username, password = creds.split(":")

            user = self.get_user(options['param'])
            if user.sms_data:
                backend = user.sms_data
            else:
                backend = SMSBackendData()
                backend.limit = options.get("sms_limit", 10)
                print "SMS deliveries limit is set to 10"

            backend.credentials = "%s:%s" % (username, password)
            backend.sender = sender
            backend.save()
            user.sms_data = backend
            user.save()

        if options.get("sms_limit"):
            user = self.get_user(options['param'])
            user.sms_data.limit = options.get("sms_limit")
            user.sms_data.save()

        if options.get('create_user'):
            username = options['param'].strip()
            superadmin = options.get('superuser', False)
            manager = options.get('manager', False)
            name = options.get('name', None)

            try:
                existing = User.objects.get(user_id=username)
            except User.DoesNotExist:
                existing = False

            if existing:
                print "User %s, already exists" % username
                exit()

            inst_pk = options.get('institution')
            if not inst_pk:
                print "Please provide an institution id using --institution"
                exit()
            inst = Institution.objects.get(pk=int(inst_pk))

            password = getpass.getpass("Password:")
            password_confirm = getpass.getpass("Confirm password:")

            if password != password_confirm:
                print "Passwords don't match"
                exit()

            newuser = User()
            newuser.user_type = "password"
            newuser.admin_p = True
            newuser.info = {'name': name or username, 'password':
                            make_password(password)}
            newuser.name = name
            newuser.user_id = username
            newuser.superadmin_p = superadmin
            newuser.management_p = manager
            newuser.institution = inst
            newuser.ecounting_account = False
            newuser.save()
            newuser.user_groups.set([UserGroup.objects.get(name="default")])
