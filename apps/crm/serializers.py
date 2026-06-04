from rest_framework import serializers
from apps.crm.models import Customer, Deal, HubspotSyncLog


class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    deal_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "identifier", "account", "hubspot_contact_id",
            "email", "first_name", "last_name", "full_name",
            "phone", "lifecycle_stage", "synced_at", "is_deleted",
            "deal_count", "created", "updated",
        ]
        read_only_fields = [
            "identifier", "account", "synced_at", "created", "updated",
        ]

    def get_deal_count(self, obj):
        return obj.deals.filter(is_deleted=False).count()


class DealSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(source="customer.email", read_only=True)

    class Meta:
        model = Deal
        fields = [
            "identifier", "account", "customer", "customer_email",
            "hubspot_deal_id", "deal_name", "amount", "currency",
            "stage", "closed_won_at", "expected_close_date",
            "synced_at", "is_deleted", "created", "updated",
        ]
        read_only_fields = [
            "identifier", "account", "synced_at", "created", "updated",
        ]


class DealDetailSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = [
            "identifier", "account", "customer", "customer_email",
            "customer_name", "hubspot_deal_id", "deal_name",
            "amount", "currency", "stage", "closed_won_at",
            "synced_at", "raw_properties", "created", "updated",
        ]
        read_only_fields = [
            "identifier", "account", "synced_at", "created", "updated",
        ]

    def get_customer_name(self, obj):
        if obj.customer:
            return obj.customer.full_name
        return None


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HubspotSyncLog
        fields = [
            "identifier", "entity_type", "sync_started_at",
            "sync_ended_at", "records_created", "records_updated",
            "status", "error_message", "created",
        ]
