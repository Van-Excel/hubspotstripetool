from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import CommonField

User = get_user_model()


class ReconciliationRun(CommonField):
    STATUS_CHOICES = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="reconciliation_runs"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    deals_processed = models.IntegerField(default=0)
    transactions_processed = models.IntegerField(default=0)
    anomalies_found = models.IntegerField(default=0)
    triggered_by = models.CharField(max_length=20, default="scheduled")
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created"]


class Anomaly(CommonField):
    ANOMALY_TYPES = [
        ("missing_payment", "Missing Payment"),
        ("amount_mismatch", "Amount Mismatch"),
        ("overpayment", "Overpayment"),
        ("status_mismatch", "Status Mismatch"),
    ]

    SEVERITY_CHOICES = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]

    reconciliation_run = models.ForeignKey(
        ReconciliationRun, on_delete=models.CASCADE, related_name="anomalies"
    )
    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="anomalies"
    )
    deal = models.ForeignKey(
        "crm.Deal", on_delete=models.SET_NULL, null=True, blank=True, related_name="anomalies"
    )
    payment_transaction = models.ForeignKey(
        "payments.PaymentTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anomalies",
    )
    anomaly_type = models.CharField(max_length=50, choices=ANOMALY_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    expected_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    expected_status = models.CharField(max_length=50, blank=True)
    actual_status = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    @property
    def is_resolved(self):
        return hasattr(self, "resolution")

    class Meta:
        ordering = ["-created"]


class Resolution(CommonField):
    RESOLUTION_TYPES = [
        ("adjust_deal", "Adjust Deal"),
        ("refund", "Refund"),
        ("manual_review", "Manual Review"),
        ("ignore", "Ignore"),
    ]

    anomaly = models.OneToOneField(
        Anomaly, on_delete=models.CASCADE, related_name="resolution"
    )
    resolved_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="resolved_anomalies"
    )
    resolution_type = models.CharField(max_length=50, choices=RESOLUTION_TYPES)
    notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
