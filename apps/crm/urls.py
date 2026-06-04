from django.urls import path
from apps.crm.views import (
    CustomerListView,
    CustomerDetailView,
    DealListView,
    DealDetailView,
    SyncTriggerView,
    SyncLogView,
)

app_name = "crm"

urlpatterns = [
    path("customers/", CustomerListView.as_view(), name="customer-list"),
    path("customers/<uuid:pk>/", CustomerDetailView.as_view(), name="customer-detail"),
    path("deals/", DealListView.as_view(), name="deal-list"),
    path("deals/<uuid:pk>/", DealDetailView.as_view(), name="deal-detail"),
    path("sync/", SyncTriggerView.as_view(), name="sync-trigger"),
    path("sync/logs/", SyncLogView.as_view(), name="sync-logs"),
]
