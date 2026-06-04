import json
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Q

from apps.accounts.permissions import HasPermission
from apps.payments.models import PaymentTransaction
from apps.payments.serializers import PaymentTransactionSerializer, PaymentStatsSerializer
from apps.payments.tasks import sync_stripe_payments, handle_stripe_webhook
from apps.payments.services.stripe_client import StripeClient


class PaymentSyncView(APIView):
    permission_classes = [HasPermission("trigger_sync")]

    def post(self, request):
        task = sync_stripe_payments.delay()
        return Response(
            {"message": "Stripe payment sync started", "task_id": task.id},
            status=status.HTTP_202_ACCEPTED,
        )


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

        handle_stripe_webhook.delay(event_data)
        return Response({"status": "received"}, status=status.HTTP_200_OK)
