"""
"""
import yaml
import uuid

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

class Command(BaseCommand):
    args = ''
    help = 'Import poll ballots from yaml'

    @transaction.atomic
    def handle(self, *args, **options):
        election = Election.objects.get(uuid=args[0])
        data = yaml.load(file(args[1]))
        for poll_data in data:
            poll = election.polls.get(uuid=poll_data.get('uuid'))
            voter_data = u'\n'.join(poll_data.get('voters'))
            voters = iter_voter_data(StringIO(voter_data))
            ids = []
            for voter_data in voters:
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
                    voter.uuid = str(uuid.uuid4())
                    voter.init_audit_passwords()
                    voter.generate_password()
                voter.save()


            existing = poll.voters.all()
            for voter in existing.exclude(voter_login_id__in=ids):
                print u"Stray voter: {}: {}".format(poll.uuid, voter.zeus_string)

