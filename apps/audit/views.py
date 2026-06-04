from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.accounts.permissions import HasPermission
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    permission_classes = [HasPermission("view_audit_logs")]
    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["action", "entity_type"]
    ordering_fields = ["created", "action"]
    ordering = ["-created"]
