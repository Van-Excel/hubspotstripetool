from rest_framework import serializers
from apps.reconciliation.models import ReconciliationRun, Anomaly, Resolution


class ResolutionSerializer(serializers.ModelSerializer):
    resolved_by_email = serializers.EmailField(source="resolved_by.email", read_only=True)

    class Meta:
        model = Resolution
        fields = [
            "identifier", "resolution_type", "notes",
            "resolved_by", "resolved_by_email", "resolved_at",
        ]
        read_only_fields = ["identifier", "resolved_at"]


class AnomalySerializer(serializers.ModelSerializer):
    resolution = ResolutionSerializer(read_only=True)
    deal_name = serializers.CharField(source="deal.deal_name", read_only=True, default=None)
    customer_email = serializers.SerializerMethodField()
    is_resolved = serializers.BooleanField(read_only=True)

    class Meta:
        model = Anomaly
        fields = [
            "identifier", "reconciliation_run", "deal",
            "payment_transaction", "anomaly_type", "severity",
            "expected_amount", "actual_amount", "expected_status",
            "actual_status", "description", "deal_name",
            "customer_email", "is_resolved", "resolution", "created",
        ]
        read_only_fields = ["identifier", "created"]

    def get_customer_email(self, obj):
        if obj.deal and obj.deal.customer:
            return obj.deal.customer.email
        return None


class ReconciliationRunSerializer(serializers.ModelSerializer):
    anomaly_count = serializers.SerializerMethodField()

    class Meta:
        model = ReconciliationRun
        fields = [
            "identifier", "status", "deals_processed",
            "transactions_processed", "anomalies_found",
            "triggered_by", "started_at", "ended_at",
            "error_message", "anomaly_count", "created",
        ]

    def get_anomaly_count(self, obj):
        return obj.anomalies.count()


class DashboardSerializer(serializers.Serializer):
    total_anomalies = serializers.IntegerField()
    unresolved_anomalies = serializers.IntegerField()
    resolved_anomalies = serializers.IntegerField()
    by_type = serializers.DictField(child=serializers.IntegerField())
    by_severity = serializers.DictField(child=serializers.IntegerField())
    last_run_at = serializers.DateTimeField(allow_null=True)
