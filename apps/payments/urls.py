from django.urls import path
from apps.payments.views import (
    PaymentSyncView,
    PaymentTransactionListView,
    PaymentTransactionDetailView,
    PaymentStatsView,
    StripeWebhookView,
)

app_name = "payments"

urlpatterns = [
    path("sync/", PaymentSyncView.as_view(), name="payment-sync"),
    path("", PaymentTransactionListView.as_view(), name="payment-list"),
    path("<uuid:pk>/", PaymentTransactionDetailView.as_view(), name="payment-detail"),
    path("stats/", PaymentStatsView.as_view(), name="payment-stats"),
    path("webhook/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
