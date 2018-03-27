from __future__ import print_function
from django.core.management.base import BaseCommand

from helios.models import Election, CastVote

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class Command(BaseCommand):
    args = ''
    delimiter = ";"
    help = 'Export election votes to csv format'

    def handle(self, *args, **options):
        election = Election.objects.get(uuid=args[0])
        for poll in election.polls.all():
            print(poll.name)
            for vote in CastVote.objects.filter(voter__excluded_at__isnull=True,
                                           poll=poll).order_by('voter__voter_surname',
                                                                       'cast_at'):
                print(u"%s%s%s" % (vote.voter.full_name, self.delimiter, vote.cast_at))
