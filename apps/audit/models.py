from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import CommonField

User = get_user_model()


class AuditLog(CommonField):
    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="audit_logs"
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=64)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        user_email = self.user.email if self.user else "system"
        return f"[{user_email}] {self.action} {self.entity_type}#{self.entity_id}"
