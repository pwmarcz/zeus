# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('heliosauth', '0003_data_user_groups'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSBackendData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('credentials', models.TextField(default=None, max_length=255, null=True)),
                ('limit', models.PositiveIntegerField(default=0)),
                ('sent', models.PositiveIntegerField(default=0)),
                ('sender', models.CharField(default=b'ZEUS', max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='user',
            name='sms_data',
            field=models.ForeignKey(default=None, to='heliosauth.SMSBackendData', on_delete=models.CASCADE, null=True),
            preserve_default=True,
        ),
    ]
