

from django.core.management.base import BaseCommand

from zeus.models import Institution


institution_row = "%-3d %-70s %-2d"
institution_row_header = "%-3s %-70s %-2s"


class Command(BaseCommand):
    args = ''
    help = 'List institutions'

    def handle(self, *args, **options):
        print(institution_row_header % ('ID', 'NAME', 'USERS'))
        for inst in Institution.objects.all():
            users_count = inst.user_set.count()
            print(institution_row % (inst.pk, inst.name, users_count))
