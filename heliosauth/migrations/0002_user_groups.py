# -*- coding: utf-8 -*-



from django.db import models, migrations
import helios.fields
import heliosauth.models


class Migration(migrations.Migration):

    dependencies = [
        ('heliosauth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('election_types', helios.fields.SeparatedValuesField(default=heliosauth.models.default_election_types_modules, max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='user',
            name='user_groups',
            field=models.ManyToManyField(to='heliosauth.UserGroup'),
            preserve_default=True,
        ),
    ]
