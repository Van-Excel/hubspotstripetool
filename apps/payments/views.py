import json
import os
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Q

from apps.accounts.permissions import HasPermission
from apps.payments.models import PaymentTransaction
from apps.payments.serializers import PaymentTransactionSerializer, PaymentStatsSerializer
from apps.payments.services.stripe_client import StripeClient
from apps.accounts.models import Account
import stripe


class PaymentSyncView(APIView):
    permission_classes = [HasPermission("trigger_sync")]

    def post(self, request):
        account = Account.objects.first()
        if not account:
            return Response({"error": "No account found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        imported = 0
        from apps.payments.models import PaymentProviderRecord
        from django.utils import timezone
        try:
            for pi in stripe.PaymentIntent.list(limit=100).auto_paging_iter():
                pi_id = pi.id
                email = pi.receipt_email or ""
                amount = float(pi.amount) / 100
                status = "succeeded" if pi.status == "succeeded" else "failed"
                tx, _ = PaymentTransaction.objects.update_or_create(
                    stripe_payment_intent_id=pi_id,
                    defaults={
                        "account": account,
                        "customer_email": email,
                        "amount": amount,
                        "currency": pi.currency or "usd",
                        "provider": "stripe",
                        "status": status,
                        "raw_data": pi.to_dict() if hasattr(pi, "to_dict") else {},
                        "synced_at": timezone.now(),
                    },
                )
                PaymentProviderRecord.objects.update_or_create(
                    transaction=tx,
                    defaults={
                        "provider_payment_id": pi_id,
                        "provider_status": pi.status,
                        "amount_charged": amount,
                        "webhook_received_at": timezone.now(),
                    },
                )
                imported += 1
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": f"Stripe sync complete", "imported": imported})


class PaymentTransactionListView(generics.ListAPIView):
    permission_classes = [HasPermission("view_payments")]
    queryset = PaymentTransaction.objects.select_related("provider_record", "deal").all()
    serializer_class = PaymentTransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "provider", "currency"]
    search_fields = ["customer_email", "stripe_payment_intent_id"]
    ordering_fields = ["amount", "created", "status"]


class PaymentTransactionDetailView(generics.RetrieveAPIView):
    permission_classes = [HasPermission("view_payments")]
    queryset = PaymentTransaction.objects.select_related("provider_record", "deal").all()
    serializer_class = PaymentTransactionSerializer


class PaymentStatsView(APIView):
    permission_classes = [HasPermission("view_payments")]

    def get(self, request):
        qs = PaymentTransaction.objects.all()
        stats = {
            "total_transactions": qs.count(),
            "total_succeeded": qs.filter(status="succeeded").count(),
            "total_failed": qs.filter(status="failed").count(),
            "total_amount_succeeded": (
                qs.filter(status="succeeded").aggregate(total=Sum("amount"))["total"] or 0
            ),
            "by_provider": {
                "stripe": qs.filter(provider="stripe").count(),
                "flutterwave": qs.filter(provider="flutterwave").count(),
            },
        }
        serializer = PaymentStatsSerializer(stats)
        return Response(serializer.data)


class StripeWebhookView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        payload = request.body
        signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        client = StripeClient()
        if not client.verify_webhook_signature(payload, signature):
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_data = json.loads(payload)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

        event_type = event_data.get("type", "")
        data = event_data.get("data", {}).get("object", {})

        if event_type in ("payment_intent.succeeded", "payment_intent.payment_failed"):
            pi_id = data.get("id", "")
            if pi_id:
                try:
                    tx = PaymentTransaction.objects.get(stripe_payment_intent_id=pi_id)
                    tx.status = "succeeded" if event_type.endswith("succeeded") else "failed"
                    tx.save(update_fields=["status", "updated"])
                except PaymentTransaction.DoesNotExist:
                    pass

        return Response({"status": "received"}, status=status.HTTP_200_OK)
