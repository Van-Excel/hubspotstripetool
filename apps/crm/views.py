from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.accounts.permissions import HasPermission
from apps.crm.models import Customer, Deal, HubspotSyncLog
from apps.crm.serializers import (
    CustomerSerializer,
    DealSerializer,
    DealDetailSerializer,
    SyncLogSerializer,
)
from apps.crm.services.hubspot_client import HubSpotClient
from apps.crm.services.sync import sync_owners, sync_contacts, sync_deals
from apps.accounts.models import Account


class CustomerListView(generics.ListAPIView):
    permission_classes = [HasPermission("view_customers")]
    queryset = Customer.objects.select_related("owner").filter(is_deleted=False)
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["lifecycle_stage"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created", "email", "first_name", "last_name"]


class CustomerDetailView(generics.RetrieveAPIView):
    permission_classes = [HasPermission("view_customers")]
    queryset = Customer.objects.select_related("owner").filter(is_deleted=False)
    serializer_class = CustomerSerializer


class DealListView(generics.ListAPIView):
    permission_classes = [HasPermission("view_deals")]
    queryset = Deal.objects.select_related("customer").filter(is_deleted=False)
    serializer_class = DealSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["stage", "currency"]
    search_fields = ["deal_name", "customer__email"]
    ordering_fields = ["amount", "created", "closed_won_at", "deal_name"]


class DealDetailView(generics.RetrieveAPIView):
    permission_classes = [HasPermission("view_deals")]
    queryset = Deal.objects.select_related("customer").filter(is_deleted=False)
    serializer_class = DealDetailSerializer


class SyncTriggerView(APIView):
    permission_classes = [HasPermission("trigger_sync")]

    def post(self, request):
        account = Account.objects.first()
        if not account:
            return Response({"error": "No account found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        client = HubSpotClient()
        log1 = sync_owners(account, client)
        log2 = sync_contacts(account, client)
        log3 = sync_deals(account, client)
        return Response({
            "message": "HubSpot sync complete",
            "contacts": f"{log2.records_created} created, {log2.records_updated} updated",
            "deals": f"{log3.records_created} created, {log3.records_updated} updated",
        })


class SyncLogView(generics.ListAPIView):
    permission_classes = [HasPermission("trigger_sync")]
    queryset = HubspotSyncLog.objects.all()
    serializer_class = SyncLogSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["entity_type", "status"]
    ordering_fields = ["created", "sync_started_at"]
