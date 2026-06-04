import pytest
from django.contrib.auth import get_user_model
from apps.accounts.models import Account, Role, Permission

User = get_user_model()


class TestUserModel:
    def test_create_user(self, db):
        user = User.objects.create_user(
            email="john@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )
        assert user.email == "john@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.check_password("testpass123")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.identifier is not None

    def test_create_superuser(self, db):
        user = User.objects.create_superuser(
            email="super@example.com",
            password="testpass123",
            first_name="Super",
            last_name="User",
        )
        assert user.is_superuser is True
        assert user.is_staff is True

    def test_email_required(self, db):
        with pytest.raises(ValueError, match="Email is required"):
            User.objects.create_user(email="", password="test")

    def test_email_unique(self, db):
        User.objects.create_user(email="dup@example.com", password="test")
        with pytest.raises(Exception):
            User.objects.create_user(email="dup@example.com", password="test")

    def test_username_is_none(self, db):
        user = User.objects.create_user(email="nouser@example.com", password="test")
        assert user.username is None

    def test_full_name(self, db):
        user = User.objects.create_user(
            email="name@example.com",
            password="test",
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"

    def test_full_name_no_last_name(self, db):
        user = User.objects.create_user(
            email="single@example.com",
            password="test",
            first_name="John",
            last_name="",
        )
        assert user.full_name == "John"

    def test_str_returns_email(self, db):
        user = User.objects.create_user(email="str@example.com", password="test")
        assert str(user) == "str@example.com"


class TestAccountModel:
    def test_create_account(self, db, role_admin):
        user = User.objects.create_user(email="acc@example.com", password="test")
        account = Account.objects.create(user=user, role=role_admin)
        assert account.user == user
        assert account.role == role_admin
        assert account.is_active is True
        assert account.identifier is not None

    def test_one_to_one_user(self, db, role_admin):
        user = User.objects.create_user(email="onetoone@example.com", password="test")
        Account.objects.create(user=user, role=role_admin)
        with pytest.raises(Exception):
            Account.objects.create(user=user, role=role_admin)

    def test_str_uses_full_name(self, db, role_admin):
        user = User.objects.create_user(
            email="str2@example.com",
            password="test",
            first_name="Jane",
            last_name="Smith",
        )
        account = Account.objects.create(user=user, role=role_admin)
        assert str(account) == "Jane Smith"

    def test_account_deactivation(self, db, role_admin):
        user = User.objects.create_user(email="deact@example.com", password="test")
        account = Account.objects.create(user=user, role=role_admin)
        account.is_active = False
        account.save()
        account.refresh_from_db()
        assert account.is_active is False


class TestRoleModel:
    def test_role_has_permissions(self, db, role_admin, permissions):
        admin_perms = set(role_admin.permissions.values_list("codename", flat=True))
        assert "manage_users" in admin_perms
        assert "trigger_sync" in admin_perms

    def test_analyst_permissions(self, db, role_analyst):
        analyst_perms = set(role_analyst.permissions.values_list("codename", flat=True))
        assert "manage_users" not in analyst_perms
        assert "resolve_anomalies" in analyst_perms

    def test_viewer_permissions(self, db, role_viewer):
        viewer_perms = set(role_viewer.permissions.values_list("codename", flat=True))
        assert "view_customers" in viewer_perms
        assert "resolve_anomalies" not in viewer_perms
        assert "manage_users" not in viewer_perms

    def test_role_name_unique(self, db):
        with pytest.raises(Exception):
            Role.objects.create(name="admin")


class TestPermissionModel:
    def test_permission_codename_unique(self, db):
        with pytest.raises(Exception):
            Permission.objects.create(codename="manage_users", name="Duplicate")


class TestCommonField:
    def test_identifier_is_uuid7(self, db):
        user = User.objects.create_user(email="uuid@example.com", password="test")
        assert len(str(user.identifier)) == 36
        assert str(user.identifier).count("-") == 4

    def test_created_auto_set(self, db):
        user = User.objects.create_user(email="created@example.com", password="test")
        assert user.created is not None

    def test_updated_auto_set(self, db):
        user = User.objects.create_user(email="updated@example.com", password="test")
        assert user.updated is not None

    def test_old_id_default_zero(self, db):
        user = User.objects.create_user(email="oldid@example.com", password="test")
        assert user.old_id == 0
