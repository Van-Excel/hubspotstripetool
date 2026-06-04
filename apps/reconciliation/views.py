from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Count, Q

from apps.accounts.permissions import HasPermission
from apps.reconciliation.models import ReconciliationRun, Anomaly, Resolution
from apps.reconciliation.engine import ReconciliationEngine
from apps.accounts.models import Account
from apps.reconciliation.serializers import (
    ReconciliationRunSerializer,
    AnomalySerializer,
    DashboardSerializer,
)


class ReconciliationRunTriggerView(APIView):
    permission_classes = [HasPermission("run_reconciliation")]

    def post(self, request):
        account = Account.objects.first()
        if not account:
            return Response({"error": "No account found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        engine = ReconciliationEngine()
        run = engine.run(account)
        return Response({
            "message": "Reconciliation complete",
            "anomalies_found": run.anomalies_found,
            "deals_processed": run.deals_processed,
        })


class RunHistoryView(generics.ListAPIView):
    permission_classes = [HasPermission("view_anomalies")]
    queryset = ReconciliationRun.objects.prefetch_related("anomalies").all()
    serializer_class = ReconciliationRunSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "triggered_by"]
    ordering_fields = ["created", "started_at"]
    ordering = ["-created"]


class RunDetailView(generics.RetrieveAPIView):
    permission_classes = [HasPermission("view_anomalies")]
    queryset = ReconciliationRun.objects.prefetch_related("anomalies").all()
    serializer_class = ReconciliationRunSerializer


class AnomalyListView(generics.ListAPIView):
    permission_classes = [HasPermission("view_anomalies")]
    queryset = Anomaly.objects.select_related(
        "deal__customer", "payment_transaction"
    ).prefetch_related("resolution").all()
    serializer_class = AnomalySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["anomaly_type", "severity"]
    ordering_fields = ["created", "severity", "expected_amount", "anomaly_type"]
    ordering = ["-created"]


class AnomalyDetailView(generics.RetrieveAPIView):
    permission_classes = [HasPermission("view_anomalies")]
    queryset = Anomaly.objects.select_related(
        "deal__customer", "payment_transaction"
    ).prefetch_related("resolution").all()
    serializer_class = AnomalySerializer


class AnomalyResolveView(APIView):
    permission_classes = [HasPermission("resolve_anomalies")]

    def post(self, request, pk):
        try:
            anomaly = Anomaly.objects.select_related("deal__customer").get(identifier=pk)
        except Anomaly.DoesNotExist:
            return Response({"error": "Anomaly not found"}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(anomaly, "resolution"):
            return Response({"error": "Anomaly already resolved"}, status=status.HTTP_400_BAD_REQUEST)

        resolution_type = request.data.get("resolution_type", "manual_review")
        notes = request.data.get("notes", "")

        resolution = Resolution.objects.create(
            anomaly=anomaly,
            resolved_by=request.user,
            resolution_type=resolution_type,
            notes=notes,
        )

        from apps.audit.services import log_action
        log_action(
            user=request.user,
            action="resolve_anomaly",
            entity_type="anomaly",
            entity_id=str(anomaly.identifier),
            new_values={"resolution_type": resolution_type, "notes": notes},
        )

        return Response(
            {"message": "Anomaly resolved", "resolution_id": str(resolution.identifier)},
            status=status.HTTP_200_OK,
        )


class DashboardView(APIView):
    permission_classes = [HasPermission("view_dashboard")]

    def get(self, request):
        anomalies = Anomaly.objects.all()
        resolved = anomalies.exclude(resolution__isnull=True)

        by_type = dict(
            anomalies.values_list("anomaly_type").annotate(count=Count("identifier")).order_by()
        )
        by_severity = dict(
            anomalies.values_list("severity").annotate(count=Count("identifier")).order_by()
        )

        last_run = ReconciliationRun.objects.filter(
            status="completed"
        ).order_by("-created").first()

        data = {
            "total_anomalies": anomalies.count(),
            "unresolved_anomalies": anomalies.filter(resolution__isnull=True).count(),
            "resolved_anomalies": resolved.count(),
            "by_type": by_type if by_type else {},
            "by_severity": by_severity if by_severity else {},
            "last_run_at": last_run.created if last_run else None,
        }
        serializer = DashboardSerializer(data)
        return Response(serializer.data)
