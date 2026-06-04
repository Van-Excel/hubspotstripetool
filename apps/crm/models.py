from django.db import models
from apps.core.models import CommonField


class HubspotOwner(CommonField):
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="hubspot_owners",
    )
    hubspot_owner_id = models.CharField(max_length=64, unique=True, db_index=True)
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.full_name or self.email

    class Meta:
        ordering = ["last_name", "first_name"]


class Customer(CommonField):
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="customers",
    )
    owner = models.ForeignKey(
        HubspotOwner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
    )
    hubspot_contact_id = models.CharField(max_length=64, unique=True, db_index=True)
    email = models.EmailField(db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    lifecycle_stage = models.CharField(max_length=50, blank=True)
    raw_properties = models.JSONField(default=dict, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.full_name or self.email

    class Meta:
        ordering = ["last_name", "first_name"]


class Deal(CommonField):
    STAGE_CHOICES = [
        ("appointmentscheduled", "Appointment Scheduled"),
        ("qualifiedtobuy", "Qualified to Buy"),
        ("presentationscheduled", "Presentation Scheduled"),
        ("decisionmakerboughtin", "Decision Maker Bought In"),
        ("contractsent", "Contract Sent"),
        ("closedwon", "Closed Won"),
        ("closedlost", "Closed Lost"),
    ]

    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="deals",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
    )
    owner = models.ForeignKey(
        HubspotOwner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
    )
    hubspot_deal_id = models.CharField(max_length=64, unique=True, db_index=True)
    deal_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES)
    closed_won_at = models.DateTimeField(null=True, blank=True)
    expected_close_date = models.DateField(null=True, blank=True)
    raw_properties = models.JSONField(default=dict, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.deal_name} (${self.amount})"

    class Meta:
        ordering = ["-created"]


class HubspotSyncLog(CommonField):
    class EntityType(models.TextChoices):
        CONTACT = "contact", "Contact"
        DEAL = "deal", "Deal"
        OWNER = "owner", "Owner"

    class SyncStatus(models.TextChoices):
        SUCCESS = "success", "Success"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"
        RUNNING = "running", "Running"

    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="hubspot_sync_logs",
    )
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    sync_started_at = models.DateTimeField(null=True, blank=True)
    sync_ended_at = models.DateTimeField(null=True, blank=True)
    last_cursor = models.CharField(max_length=255, blank=True)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=SyncStatus.choices, default=SyncStatus.RUNNING
    )
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.entity_type} sync — {self.status} ({self.records_created} new, {self.records_updated} updated)"

    class Meta:
        ordering = ["-created"]
