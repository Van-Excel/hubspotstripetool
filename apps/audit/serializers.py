from rest_framework import serializers
from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "identifier", "action", "entity_type", "entity_id",
            "user_email", "old_values", "new_values",
            "ip_address", "created",
        ]
