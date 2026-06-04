from django.db import migrations


PERMISSIONS = [
    ("manage_users", "Manage Users", "Create, deactivate, and change user roles"),
    ("trigger_sync", "Trigger Data Sync", "Trigger HubSpot and Stripe data syncs"),
    ("view_customers", "View Customers", "List and view customer data"),
    ("view_deals", "View Deals", "List and view deal data"),
    ("view_payments", "View Payments", "List and view payment transactions"),
    ("view_anomalies", "View Anomalies", "List and view anomaly records"),
    ("resolve_anomalies", "Resolve Anomalies", "Mark anomalies as resolved"),
    ("run_reconciliation", "Run Reconciliation", "Trigger reconciliation engine"),
    ("view_audit_logs", "View Audit Logs", "List and filter audit trail"),
    ("view_dashboard", "View Dashboard", "Access summary dashboard"),
]

ROLES = {
    "admin": [
        "manage_users",
        "trigger_sync",
        "view_customers",
        "view_deals",
        "view_payments",
        "view_anomalies",
        "resolve_anomalies",
        "run_reconciliation",
        "view_audit_logs",
        "view_dashboard",
    ],
    "analyst": [
        "trigger_sync",
        "view_customers",
        "view_deals",
        "view_payments",
        "view_anomalies",
        "resolve_anomalies",
        "run_reconciliation",
        "view_audit_logs",
        "view_dashboard",
    ],
    "viewer": [
        "view_customers",
        "view_deals",
        "view_payments",
        "view_anomalies",
        "view_dashboard",
    ],
}


def seed_roles_and_permissions(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")

    perm_map = {}
    for codename, name, desc in PERMISSIONS:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={"name": name, "description": desc},
        )
        perm_map[codename] = perm

    for role_name, perm_codenames in ROLES.items():
        role, created = Role.objects.get_or_create(
            name=role_name,
            defaults={"description": f"{role_name.title()} role"},
        )
        if created:
            role.permissions.set([perm_map[c] for c in perm_codenames])


def remove_roles_and_permissions(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(name__in=ROLES.keys()).delete()
    Permission.objects.filter(codename__in=[p[0] for p in PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles_and_permissions, remove_roles_and_permissions),
    ]
