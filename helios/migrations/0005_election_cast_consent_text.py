# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0004_sms_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='cast_consent_text',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
