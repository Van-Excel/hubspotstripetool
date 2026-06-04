import pytest
from django.contrib.auth import get_user_model
from apps.accounts.models import Account, Role, Permission

User = get_user_model()


@pytest.fixture
def role_admin(db):
    return Role.objects.get(name="admin")


@pytest.fixture
def role_analyst(db):
    return Role.objects.get(name="analyst")


@pytest.fixture
def role_viewer(db):
    return Role.objects.get(name="viewer")


@pytest.fixture
def permissions(db):
    return list(Permission.objects.all())


@pytest.fixture
def user_admin(db, role_admin):
    user = User.objects.create_user(
        email="testadmin@example.com",
        password="testpass123",
        first_name="Test",
        last_name="Admin",
    )
    Account.objects.create(user=user, role=role_admin)
    return user


@pytest.fixture
def user_analyst(db, role_analyst):
    user = User.objects.create_user(
        email="testanalyst@example.com",
        password="testpass123",
        first_name="Test",
        last_name="Analyst",
    )
    Account.objects.create(user=user, role=role_analyst)
    return user


@pytest.fixture
def user_viewer(db, role_viewer):
    user = User.objects.create_user(
        email="testviewer@example.com",
        password="testpass123",
        first_name="Test",
        last_name="Viewer",
    )
    Account.objects.create(user=user, role=role_viewer)
    return user


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def auth_client(api_client, user_admin):
    api_client.force_authenticate(user=user_admin)
    return api_client
