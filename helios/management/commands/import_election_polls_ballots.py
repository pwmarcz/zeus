"""
"""

import yaml

from django.db import transaction
from django.core.management.base import BaseCommand

from helios.models import Election, Poll


class Command(BaseCommand):
    args = ''
    help = 'Import poll ballots from yaml'

    @transaction.atomic
    def handle(self, *args, **options):
        election = Election.objects.get(uuid=args[0])
        with open(args[1]) as f:
            data = yaml.load(f)
        for poll_data in data:
            if not poll_data.get('uuid', None):
                poll = Poll(election=election)
            else:
                poll = election.polls.get(uuid=poll_data.get('uuid'))
            poll.name = poll_data.get('name')

            questions = poll_data.get('questions')
            questions_data = []
            for qdata in questions:
                question = qdata.get('question')
                answers = qdata.get('answers')
                _min, _max = qdata.get('min', 1), qdata.get('max', 1)
                q = {
                    'choice_type': 'choice',
                    'question': question,
                    'max_answers': _max,
                    'min_answers': _min,
                    'answers': answers
                }
                for i, ans in enumerate(answers):
                    q['answer_%d' % i] = ans
                questions_data.append(q)
            poll.questions_data = questions_data
            poll.update_answers()
            poll.save()
            poll_data['uuid'] = str(poll.uuid)

        with open(args[1], 'w') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
