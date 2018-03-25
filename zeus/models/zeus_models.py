from django.db import models


class Institution(models.Model):
    name = models.CharField(max_length=255, unique=True)
    ecounting_id = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'zeus'
