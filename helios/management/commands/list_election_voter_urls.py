

from django.core.management.base import BaseCommand

from helios.models import Voter


class Command(BaseCommand):
    args = ''
    help = 'List the voter login urls'

    def handle(self, *args, **options):
        if args:
            voters = Voter.objects.filter(poll__election__uuid=args[0])
        else:
            voters = Voter.objects.all()

        for v in voters:
            if not v.excluded_at:
                print(v.get_quick_login_url())
        # once broken out of the while loop, quit and wait for next invocation
        # this happens when there are no votes left to verify
