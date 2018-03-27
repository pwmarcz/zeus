"""
"""
from __future__ import absolute_import
import yaml

from django.db import transaction
from django.core.management.base import BaseCommand

from helios.models import Election


import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class Command(BaseCommand):
    args = ''
    help = 'Import poll ballots from yaml'

    @transaction.atomic
    def handle(self, *args, **options):
        election = Election.objects.get(uuid=args[0])
        data = []
        for poll in election.polls.all():
            voters = []
            poll_data = {'uuid': str(poll.uuid), 'voters': voters, 'name': poll.name}
            for voter in poll.voters.filter(excluded_at__isnull=True):
                voters.append(u'{},{},{},{},{},{},{}'.format(
                    voter.voter_login_id,
                    voter.voter_email,
                    voter.voter_name,
                    voter.voter_surname,
                    voter.voter_fathername or '',
                    voter.voter_mobile or '',
                    voter.voter_weight or 1))
            data.append(poll_data)
        yaml.dump(data, sys.stdout, allow_unicode=True,
                   default_flow_style=False)
