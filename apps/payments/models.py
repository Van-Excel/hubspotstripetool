from django.db import models
from apps.core.models import CommonField


class PaymentTransaction(CommonField):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    PROVIDER_CHOICES = [
        ("stripe", "Stripe"),
        ("flutterwave", "Flutterwave"),
    ]

    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="payment_transactions"
    )
    deal = models.ForeignKey(
        "crm.Deal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transactions",
    )
    customer_email = models.EmailField(db_index=True)
    stripe_payment_intent_id = models.CharField(
        max_length=255, unique=True, blank=True, null=True, db_index=True
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default="usd")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    raw_data = models.JSONField(default=dict, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    @property
    def amount_in_dollars(self):
        return float(self.amount)

    def __str__(self):
        return f"{self.provider}:{self.status} — ${self.amount} ({self.customer_email})"

    class Meta:
        ordering = ["-created"]


class PaymentProviderRecord(CommonField):
    transaction = models.OneToOneField(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name="provider_record",
    )
    provider_payment_id = models.CharField(max_length=255)
    provider_status = models.CharField(max_length=50)
    amount_charged = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    webhook_payload = models.JSONField(default=dict, blank=True)
    webhook_received_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Provider {self.provider_payment_id} — {self.provider_status}"

    class Meta:
        ordering = ["-created"]


class QueueJobRecord(CommonField):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name="queue_jobs",
    )
    celery_task_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    enqueued_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Job {self.identifier} — {self.status}"

    class Meta:
        ordering = ["-created"]
