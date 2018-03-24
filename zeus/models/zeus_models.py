from django.db import models

from helios import models as helios_models


class Institution(models.Model):
    name = models.CharField(max_length=255, unique=True)
    ecounting_id = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'zeus'


class ElectionInfo(models.Model):
    uuid = models.CharField(max_length=50, null=False)
    _election = None

    @property
    def election(self):
        if self._election:
            return self._election
        else:
            self._election = helios_models.Election.objects.get(uuid=self.uuid)
            return self._election

    class Meta:
        app_label = 'zeus'
