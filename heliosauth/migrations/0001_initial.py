# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import heliosauth.jsonfield


class Migration(migrations.Migration):

    dependencies = [
        ('zeus', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_type', models.CharField(max_length=50)),
                ('user_id', models.CharField(unique=True, max_length=100)),
                ('name', models.CharField(max_length=200, null=True)),
                ('info', heliosauth.jsonfield.JSONField()),
                ('token', heliosauth.jsonfield.JSONField(null=True)),
                ('admin_p', models.BooleanField(default=False)),
                ('superadmin_p', models.BooleanField(default=False)),
                ('management_p', models.BooleanField(default=False)),
                ('ecounting_account', models.BooleanField(default=True)),
                ('is_disabled', models.BooleanField(default=False)),
                ('institution', models.ForeignKey(to='zeus.Institution', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='user',
            unique_together=set([('user_type', 'user_id')]),
        ),
    ]
