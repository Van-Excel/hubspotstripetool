from django.urls import path
from apps.accounts.views import UserListView, UserDetailView

app_name = "accounts_admin"

urlpatterns = [
    path("users/", UserListView.as_view(), name="admin-user-list"),
    path("users/<uuid:pk>/", UserDetailView.as_view(), name="admin-user-detail"),
]
