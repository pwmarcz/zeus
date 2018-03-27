# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0002_sms_delivery_status_20170807_1845'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='election_module',
            field=models.CharField(default=b'simple', help_text='Choose the type of the election', max_length=250, verbose_name='Election type', choices=[(b'simple', 'Simple election with one or more questions'), (b'parties', 'Party lists election'), (b'score', 'Score voting election'), (b'stv', 'Single transferable vote election'), (b'unigovgr', 'Greek Universities single governing bodies election')]),
            preserve_default=True,
        ),
    ]
