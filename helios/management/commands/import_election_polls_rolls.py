"""
"""
import yaml
import uuid

from django.forms import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.conf import settings
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from helios import utils as helios_utils
from helios.models import *

from zeus import reports
from StringIO import StringIO

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
UPDATE = os.environ.get('UPDATE_EXISTING', 0)

def validate_voter(mobile, email, throw=True):
    if not mobile:
        django_validate_email(email)
        return

    if mobile:
        mobile = mobile.replace(' ', '')
        mobile = mobile.replace('-', '')
        if len(mobile) < 4 or not mobile[1:].isdigit or \
            (mobile[0] != '+' and not mobile[0].isdigit()):
                m = "Malformed mobile phone number: %s" % mobile
                if throw:
                    raise ValidationError(m)
                else:
                    return False
    try:
        django_validate_email(email)
    except ValidationError, e:
        if throw:
            raise e
        else:
            return False
    return mobile, email

class Command(BaseCommand):
    args = ''
    help = 'Import poll ballots from yaml'

    @transaction.atomic
    def handle(self, *args, **options):
        election = Election.objects.get(uuid=args[0])
        data = yaml.load(file(args[1]))
        skip = 0
        add = 0
        voters_count = 0
        updated = 0
        for poll_data in data:
            poll = election.polls.get(uuid=poll_data.get('uuid'))
            voter_data = u'\n'.join(poll_data.get('voters'))
            voters = iter_voter_data(StringIO(voter_data))
            ids = []
            for voter_data in voters:
                voters_count += 1
                voter_id = voter_data.get('voter_id')
                ids.append(voter_id)
                existing = False
                try:
                    voter = poll.voters.get(voter_login_id=voter_id)
                    existing = True
                except Voter.DoesNotExist:
                    voter = Voter(poll=poll)

                voter.voter_login_id = voter_id
                voter.voter_email = voter_data.get('email')
                voter.voter_surname = voter_data.get('surname', None)
                voter.voter_name = voter_data.get('name', None)
                voter.voter_fathername = voter_data.get('fathername', None)
                voter.voter_mobile = voter_data.get('mobile', None)
                voter.voter_weight = voter_data.get('weight', 1)
                if not existing:
                    validate_voter(voter.voter_mobile, voter.voter_email)
                    voter.uuid = str(uuid.uuid4())
                    voter.init_audit_passwords()
                    voter.generate_password()
                    voter.save()
                    add += 1
                    print u"New voter added {}".format(voter.voter_email)
                else:
                    if UPDATE:
                        validate_voter(voter.voter_mobile, voter.voter_email)
                        updated += 1
                        voter.save()
                    else:
                        skip += 1
                        print u"Skip import of existing voter {}".format(voter.voter_email)


            existing = poll.voters.all()
            stray = 0
            for voter in existing.exclude(voter_login_id__in=ids):
                stray += 1
                print u"Stray voter {} {} ({})".format(voter.poll.name, voter.voter_login_id, voter.voter_email)

        print "Found: {}  New: {}  Existing: {}  Updated: {}  Stray: {}".format(voters_count, add, skip, updated, stray)

