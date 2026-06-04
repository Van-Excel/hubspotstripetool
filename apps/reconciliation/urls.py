from django.urls import path
from apps.reconciliation.views import (
    ReconciliationRunTriggerView,
    RunHistoryView,
    RunDetailView,
    AnomalyListView,
    AnomalyDetailView,
    AnomalyResolveView,
    DashboardView,
)

app_name = "reconciliation"

urlpatterns = [
    path("runs/", RunHistoryView.as_view(), name="run-history"),
    path("runs/<uuid:pk>/", RunDetailView.as_view(), name="run-detail"),
    path("run/", ReconciliationRunTriggerView.as_view(), name="run-trigger"),
    path("anomalies/", AnomalyListView.as_view(), name="anomaly-list"),
    path("anomalies/<uuid:pk>/", AnomalyDetailView.as_view(), name="anomaly-detail"),
    path("anomalies/<uuid:pk>/resolve/", AnomalyResolveView.as_view(), name="anomaly-resolve"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
