from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/admin/", include("apps.accounts.admin_urls")),
    path("api/crm/", include("apps.crm.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/reconciliation/", include("apps.reconciliation.urls")),
    path("api/audit/", include("apps.audit.urls")),
]
