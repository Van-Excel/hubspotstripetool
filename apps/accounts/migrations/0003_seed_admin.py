from django.db import migrations
from django.utils import timezone
from django.contrib.auth.hashers import make_password


def seed_admin_user(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Account = apps.get_model("accounts", "Account")
    Role = apps.get_model("accounts", "Role")

    admin_role = Role.objects.get(name="admin")

    user = User.objects.create(
        email="admin@reconciliation.local",
        first_name="Admin",
        last_name="User",
        is_staff=True,
        is_superuser=True,
        is_active=True,
        password=make_password("admin123"),
        date_joined=timezone.now(),
    )
    Account.objects.create(user=user, role=admin_role)


def remove_admin_user(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(email="admin@reconciliation.local").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_seed_roles_perms"),
    ]

    operations = [
        migrations.RunPython(seed_admin_user, remove_admin_user),
    ]
