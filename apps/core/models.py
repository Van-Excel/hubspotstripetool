import uuid6
from django.db import models


class CommonField(models.Model):
    identifier = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)
    old_id = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
