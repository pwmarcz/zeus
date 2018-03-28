# -*- coding: utf-8 -*-



from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('heliosauth', '0004_sms_data'),
        ('helios', '0003_auto_20171102_1509'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='cast_notify_once',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='election',
            name='sms_api_enabled',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='election',
            name='sms_data',
            field=models.ForeignKey(default=None, to='heliosauth.SMSBackendData', on_delete=models.CASCADE, null=True),
            preserve_default=True,
        ),
    ]
