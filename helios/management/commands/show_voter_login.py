"""
verify cast votes that have not yet been verified

Ben Adida
ben@adida.net
2010-05-22
"""



from django.core.management.base import BaseCommand

from helios.models import Voter

class Command(BaseCommand):
    args = ''
    help = 'Show the voter login url'

    def handle(self, *args, **options):
        for v in Voter.objects.filter(voter_email=args[0]):
            print("election uuid : %s" % v.poll.election.uuid)
            print("poll uuid : %s" % v.poll.uuid)
            print("login url : %s" % v.get_quick_login_url())
        # once broken out of the while loop, quit and wait for next invocation
        # this happens when there are no votes left to verify
