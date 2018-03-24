
from django.core.management.base import BaseCommand

from helios.models import Poll

class Command(BaseCommand):
    args = ''
    help = 'List election polls'

    def handle(self, *args, **options):
        polls = Poll.objects.filter()
        if args:
            polls = polls.filter(election__uuid=args[0])

        for p in polls:
            print p.uuid, p.short_name
