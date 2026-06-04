import pytest
from django.urls import reverse
from rest_framework import status
from apps.accounts.models import Role


class TestRegister:
    URL = reverse("accounts:register")

    def test_register_creates_user_and_account(self, db, api_client):
        resp = api_client.post(self.URL, {
            "email": "new@example.com",
            "password": "testpass123",
            "first_name": "New",
            "last_name": "User",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert "user" in resp.data
        assert "tokens" in resp.data
        assert "access" in resp.data["tokens"]
        assert "refresh" in resp.data["tokens"]
        assert resp.data["user"]["email"] == "new@example.com"
        assert resp.data["user"]["account"]["role"]["name"] == "viewer"

    def test_register_duplicate_email(self, db, api_client, user_admin):
        resp = api_client.post(self.URL, {
            "email": user_admin.email,
            "password": "testpass",
            "first_name": "Dup",
            "last_name": "User",
        }, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password(self, db, api_client):
        resp = api_client.post(self.URL, {
            "email": "short@example.com",
            "password": "123",
            "first_name": "Short",
            "last_name": "Pass",
        }, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_fields(self, db, api_client):
        resp = api_client.post(self.URL, {
            "email": "missing@example.com",
        }, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:
    URL = reverse("accounts:login")

    def test_login_valid(self, db, api_client, user_admin):
        resp = api_client.post(self.URL, {
            "email": user_admin.email,
            "password": "testpass123",
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert "tokens" in resp.data
        assert resp.data["user"]["email"] == user_admin.email

    def test_login_wrong_password(self, db, api_client, user_admin):
        resp = api_client.post(self.URL, {
            "email": user_admin.email,
            "password": "wrongpassword",
        }, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, db, api_client):
        resp = api_client.post(self.URL, {
            "email": "noone@example.com",
            "password": "whatever",
        }, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestJWTRefresh:
    def test_refresh_valid(self, db, api_client, user_admin):
        login_resp = api_client.post(reverse("accounts:login"), {
            "email": user_admin.email,
            "password": "testpass123",
        }, format="json")
        refresh = login_resp.data["tokens"]["refresh"]

        resp = api_client.post(reverse("accounts:token-refresh"), {
            "refresh": refresh,
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert "access" in resp.data


class TestMe:
    URL = reverse("accounts:me")

    def test_me_unauthenticated(self, db, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_authenticated(self, db, api_client, user_analyst):
        api_client.force_authenticate(user=user_analyst)
        resp = api_client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["email"] == user_analyst.email
        assert resp.data["full_name"] == "Test Analyst"
        assert resp.data["account"]["role"]["name"] == "analyst"


class TestAdminUsers:
    def test_list_users_as_admin(self, db, api_client, user_admin):
        api_client.force_authenticate(user=user_admin)
        url = reverse("accounts_admin:admin-user-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data["results"], list)

    def test_list_users_as_analyst_forbidden(self, db, api_client, user_analyst):
        api_client.force_authenticate(user=user_analyst)
        url = reverse("accounts_admin:admin-user-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_as_viewer_forbidden(self, db, api_client, user_viewer):
        api_client.force_authenticate(user=user_viewer)
        url = reverse("accounts_admin:admin-user-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_change_role_as_admin(self, db, api_client, user_admin, user_viewer, role_analyst):
        api_client.force_authenticate(user=user_admin)
        url = reverse("accounts_admin:admin-user-detail", args=[user_viewer.identifier])
        resp = api_client.patch(url, {"role": "analyst"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        user_viewer.account.refresh_from_db()
        assert user_viewer.account.role.name == "analyst"


class TestPermissionChecks:
    def test_has_permission_admin(self, user_admin):
        from apps.accounts.permissions import HasPermission
        perm = HasPermission("manage_users")
        assert perm.codename == "manage_users"
        assert user_admin.account.role.permissions.filter(
            codename="manage_users"
        ).exists()

    def test_has_permission_viewer_cannot_manage(self, user_viewer):
        assert not user_viewer.account.role.permissions.filter(
            codename="manage_users"
        ).exists()

    def test_has_permission_analyst_can_resolve(self, user_analyst):
        assert user_analyst.account.role.permissions.filter(
            codename="resolve_anomalies"
        ).exists()
