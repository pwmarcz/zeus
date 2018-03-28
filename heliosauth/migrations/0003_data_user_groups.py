# -*- coding: utf-8 -*-


from django.db import migrations


def default_groups(apps, schema_editor):
    DEFAULT_TYPES = ["simple", "stv", "score", "parties"]
    DEMO_TYPES = ["simple", "stv", "score", "parties"]
    Group = apps.get_model('heliosauth', 'UserGroup')
    User = apps.get_model('heliosauth', 'User')

    default, created = Group.objects.get_or_create(name="default", election_types=DEFAULT_TYPES)
    demo, created = Group.objects.get_or_create(name="demo", election_types=DEMO_TYPES)

    for user in User.objects.filter():
        is_demo = user.institution.name == 'DEMO'
        if is_demo:
            user.user_groups.add(demo)
        else:
            user.user_groups.add(default)

class Migration(migrations.Migration):

    dependencies = [
        ('heliosauth', '0002_user_groups'),
    ]

    operations = [
         migrations.RunPython(default_groups)
    ]
