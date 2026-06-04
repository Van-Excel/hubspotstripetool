from rest_framework import serializers
from apps.payments.models import PaymentTransaction, PaymentProviderRecord, QueueJobRecord


class PaymentProviderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProviderRecord
        fields = [
            "identifier", "provider_payment_id", "provider_status",
            "amount_charged", "fee_amount", "webhook_received_at", "created",
        ]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    provider_record = PaymentProviderRecordSerializer(read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            "identifier", "account", "deal", "customer_email",
            "stripe_payment_intent_id", "amount", "currency",
            "provider", "status", "synced_at",
            "provider_record", "created", "updated",
        ]
        read_only_fields = [
            "identifier", "account", "synced_at", "created", "updated",
        ]


class PaymentStatsSerializer(serializers.Serializer):
    total_transactions = serializers.IntegerField()
    total_succeeded = serializers.IntegerField()
    total_failed = serializers.IntegerField()
    total_amount_succeeded = serializers.DecimalField(max_digits=15, decimal_places=2)
    by_provider = serializers.DictField(child=serializers.IntegerField())
