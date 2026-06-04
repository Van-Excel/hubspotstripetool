# Unified Commerce Reconciliation Dashboard — Implementation Plan

## Overview

A Django REST Framework backend + React frontend that:
- Pulls customer/deal data from HubSpot's sandbox API
- Pulls payment data from Stripe (Flutterwave-ready via provider interface)
- Reconciles payments against deals via customer email matching
  (no cross-system FK exists — HubSpot is a CRM, Stripe is a payment processor)
- Flags anomalies: missing payment, amount mismatch, overpayment, status mismatch
- Architecture: **passive monitoring** tool. Deals are created in HubSpot first by the
  seed script (simulating an e-commerce/LMS platform), Stripe payments are created based
  on those deals, then our tool syncs both sides and reconciles by email.
- Provides user admin with role-based RBAC, full audit logging, monitoring endpoints
- Simple React dashboard for viewing anomalies, payments, customers, deals, and audit logs

Directly maps to ICC requirement: *"Monitor system usage, registrations, and payment workflows to identify anomalies."*

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x + Django REST Framework |
| Auth | `djangorestframework-simplejwt` (JWT) |
| Async Tasks | Celery + Redis |
| Database | PostgreSQL 16 |
| Payments | Stripe (Flutterwave-ready provider interface) |
| CRM | Real HubSpot Private App API |
| Frontend | React + Vite |
| Containerization | Docker + docker-compose |
| Pk Type | UUID v4 on all models |

---

## Conventions

- UUID v7 primary keys on all models (`CommonField` base abstract in `apps/core/models.py`)
  - Primary key field is `identifier` (not `id`)
  - All models carry `old_id`, `created`, `updated` from the base
- Django Rest Framework browsable API always available
- All data scoped to `account_id` for multi-tenant design
- Celery for all async work (sync, payment processing, reconciliation, webhook handling)
- Full audit trail via `AuditLog` model for ICC compliance requirement

---

## Directory Structure

```
hubspotandstripetool/
├── config/                          # Django project
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── dev.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py                    # Celery app config
├── apps/
│   ├── core/                        # Shared utilities
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   └── models.py               # UUIDModel base abstract class
│   ├── accounts/                    # User, Account, Role, Permission, JWT auth, RBAC
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── managers.py             # CustomUserManager (email as username)
│   │   ├── models.py               # User, Account, Role, Permission
│   │   ├── permissions.py          # HasPermission(codename) DRF class
│   │   ├── serializers.py          # Register, Login, User, Role serializers
│   │   ├── views.py                # Register, Login, Refresh, Me, User CRUD
│   │   ├── urls.py
│   │   └── migrations/
│   │       ├── 0001_initial.py
│   │       ├── 0002_seed_roles_perms.py    # Data migration: 3 roles + 11 perms
│   │       └── 0003_seed_admin.py          # Data migration: demo admin user
│   ├── crm/                         # HubSpot: Customer, Deal, sync
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py               # Customer, Deal, HubspotOwner, HubspotSyncLog
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── hubspot_client.py   # HubSpot API wrapper
│   │   │   └── sync.py             # Incremental sync logic
│   │   ├── tasks.py                # Celery: sync_hubspot_contacts, sync_hubspot_deals
│   │   ├── serializers.py          # Customer, Deal serializers
│   │   ├── views.py                # Customer list/detail, Deal list/detail, Sync trigger
│   │   ├── urls.py
│   │   └── management/commands/
│   │       └── seed_hubspot.py     # Seed fake customers & deals via HubSpot API
│   ├── payments/                    # Payment domain
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py               # PaymentTransaction, PaymentProviderRecord, QueueJobRecord
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Abstract BasePaymentProvider
│   │   │   ├── stripe_client.py    # Stripe implementation
│   │   │   └── flutterwave_client.py # Stub for future
│   │   ├── tasks.py                # Celery: process_payment, handle_webhook
│   │   ├── serializers.py          # PaymentTransaction, PaymentInitiate serializers
│   │   ├── views.py                # Initiate payment, list, detail, webhook, stats
│   │   └── urls.py
│   ├── reconciliation/              # Core reconciliation engine
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py               # ReconciliationRun, Anomaly, Resolution
│   │   ├── engine.py               # ReconciliationEngine class
│   │   ├── tasks.py                # Celery: run_reconciliation
│   │   ├── serializers.py          # Run, Anomaly, Resolution, Dashboard serializers
│   │   ├── views.py                # Trigger run, run history, anomaly list/detail/resolve, dashboard
│   │   └── urls.py
│   └── audit/                       # Audit logging
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py               # AuditLog
│       ├── services.py             # log_action() helper
│       ├── serializers.py          # AuditLogSerializer
│       ├── views.py                # Audit log listing/filtering
│       └── urls.py
├── frontend/                        # React dashboard
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx               # Entry point
│       ├── App.jsx                # Router setup
│       ├── api/
│       │   └── client.js          # Axios instance with JWT interceptor
│       ├── pages/
│       │   ├── LoginPage.jsx      # Login form, token storage
│       │   ├── DashboardPage.jsx  # Anomaly summary cards, charts
│       │   ├── AnomaliesPage.jsx  # Filterable table, resolve button
│       │   ├── PaymentsPage.jsx   # Payment transaction table
│       │   ├── CustomersPage.jsx  # Customer list
│       │   ├── DealsPage.jsx      # Deal list with payment status
│       │   ├── AuditPage.jsx      # Audit log viewer
│       │   └── AdminPage.jsx      # User management
│       └── components/
│           ├── Layout.jsx         # Navbar, sidebar, role-based menu
│           └── ProtectedRoute.jsx # Role-based route guard
├── requirements/
│   ├── base.txt  # Django, DRF, simplejwt, celery, redis, psycopg2, stripe, hubspot-api-client
│   └── dev.txt   # -r base.txt + django-extensions, pytest-django, black, ipython
├── docker-compose.yml    # db (postgres:16), redis (redis:7-alpine), web (Django)
├── Dockerfile            # Python 3.12, install deps, copy code
├── .env.example          # Template for secrets
├── .gitignore
├── manage.py
├── pytest.ini
├── TEST_PLAN.md
└── README.md
```

---

## Models

### Base Abstract Model

```python
# apps/core/models.py
import uuid6

class CommonField(models.Model):
    identifier = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)
    old_id = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

All models inherit from `CommonField` — primary key is always `identifier` (UUID v7, time-ordered), and every record gets `created`/`updated` timestamps plus `old_id` (useful for data migrations or tracking legacy IDs).

### Auth Models (`apps/accounts/models.py`)

```
User (AbstractUser)
├── identifier UUID PK (from CommonField)
├── email (unique)
├── password
├── first_name
├── last_name
├── is_active
├── is_staff
├── date_joined
├── full_name (property: first_name + last_name)
└── old_id, created, updated (from CommonField)

Account (CommonField)
├── identifier UUID PK
├── user (OneToOneField → User, unique)
├── role (ForeignKey → Role, PROTECT)
└── is_active (BooleanField, default=True)
# Name comes from user.full_name property: f"{self.user.first_name} {self.user.last_name}"

Role (CommonField)
├── identifier UUID PK
├── name CharField(50, unique)  # admin, analyst, viewer
├── description TextField
├── permissions (ManyToManyField → Permission)
└── timestamps

Permission (CommonField)
├── identifier UUID PK
├── codename CharField(100, unique)
├── name CharField(255)
├── description TextField
└── timestamps
```

**Relationships**:
- `User` 1:1 `Account` → one person, one account
- `Account` M:1 `Role` → account has a single role
- `Role` M:M `Permission` → implicit junction via Django ManyToMany

### CRM Models (`apps/crm/models.py`)

```
HubspotOwner (CommonField)
├── identifier UUID PK
├── account_id FK → Account
├── hubspot_owner_id CharField(64, unique)
├── email CharField(255)
├── first_name CharField(100)
├── last_name CharField(100)
└── timestamps

Customer (CommonField)
├── identifier UUID PK
├── account_id FK → Account
├── owner_id FK → HubspotOwner (nullable)
├── hubspot_contact_id CharField(64, unique)
├── email CharField(255, indexed)
├── first_name CharField(100)
├── last_name CharField(100)
├── phone CharField(50, blank=True)
├── lifecycle_stage CharField(50)
├── raw_properties JSONField
├── synced_at DateTimeField
├── is_deleted BooleanField(default=False)
└── timestamps

Deal (CommonField)
├── identifier UUID PK
├── account_id FK → Account
├── customer_id FK → Customer (1:M)
├── owner_id FK → HubspotOwner (nullable)
├── hubspot_deal_id CharField(64, unique)
├── deal_name CharField(255)
├── amount DecimalField(max_digits=15, decimal_places=2)
├── currency CharField(3, default='USD')
├── stage CharField(50)
├── closed_won_at DateTimeField(nullable)
├── expected_close_date DateField(nullable)
├── raw_properties JSONField
├── synced_at DateTimeField
├── is_deleted BooleanField(default=False)
└── timestamps

HubspotSyncLog (CommonField)
├── identifier UUID PK
├── account_id FK → Account
├── entity_type CharField(50)  # contact or deal
├── sync_started_at
├── sync_ended_at
├── last_cursor CharField(255, blank=True)
├── records_created IntegerField
├── records_updated IntegerField
├── status CharField(20)  # success, partial, failed
├── error_message TextField(blank=True)
└── timestamps
```

**Relationships**:
- `Account` 1:M `Customer` — one account has many customers
- `Customer` 1:M `Deal` — one customer has many deals
- `HubspotOwner` 1:M `Customer`, `HubspotOwner` 1:M `Deal`
- `Account` 1:M `HubspotSyncLog`

### Payment Models (`apps/payments/models.py`)

```
PaymentTransaction (CommonField)
├── identifier UUID PK
├── account_id FK → Account
├── deal_id FK → Deal (nullable, SET_NULL)  ← Not known at sync time; linked by reconciliation
├── customer_email CharField(255, indexed)  ← THE matching key for reconciliation
├── stripe_payment_intent_id CharField(255, unique, blank=True)  # pi_xxx from Stripe
├── amount DecimalField(max_digits=15, decimal_places=2)
├── currency CharField(3, default='USD')
├── provider CharField(20)  # stripe, flutterwave
├── status CharField(20)  # succeeded, failed, refunded (from Stripe)
├── raw_data JSONField(default=dict)  # Full Stripe PaymentIntent response
├── synced_at DateTimeField(null=True)
└── timestamps

PaymentProviderRecord (CommonField)
├── identifier UUID PK
├── transaction_id FK → PaymentTransaction (unique, 1:1, CASCADE)
├── provider_payment_id CharField(255)
├── provider_status CharField(50)
├── amount_charged DecimalField(max_digits=15, decimal_places=2, null=True)
├── fee_amount DecimalField(max_digits=10, decimal_places=2, null=True)
├── webhook_payload JSONField(default=dict)
├── webhook_received_at DateTimeField(null=True)
└── timestamps

QueueJobRecord (CommonField)
├── identifier UUID PK
├── transaction_id FK → PaymentTransaction (CASCADE)
├── celery_task_id CharField(255, blank=True)
├── status CharField(20)  # queued, processing, done, failed
├── retry_count IntegerField(default=0)
├── last_error TextField(blank=True)
├── enqueued_at DateTimeField(null=True)
├── picked_at DateTimeField(null=True)
├── completed_at DateTimeField(null=True)
└── timestamps
```

**Relationships**:
- `Deal` 1:M `PaymentTransaction` — payment linked to deal AFTER reconciliation (deal_id starts null)
- `PaymentTransaction` 1:1 `PaymentProviderRecord` — webhook data from the provider
- `PaymentTransaction` 1:M `QueueJobRecord` — tracking sync jobs (not payment creation jobs)
- **Matching key**: `PaymentTransaction.customer_email` ↔ `Customer.email`

### Reconciliation Models (`apps/reconciliation/models.py`)

```
ReconciliationRun (CommonField)
├── identifier UUID PK
├── account_id FK → Account
├── status CharField(20)  # running, completed, failed
├── deals_processed IntegerField(default=0)
├── transactions_processed IntegerField(default=0)
├── anomalies_found IntegerField(default=0)
├── triggered_by CharField(20)  # scheduled or manual
├── started_at DateTimeField(null=True)
├── ended_at DateTimeField(null=True)
├── error_message TextField(blank=True)
└── timestamps

Anomaly (CommonField)
├── identifier UUID PK
├── reconciliation_run_id FK → ReconciliationRun (CASCADE)
├── account_id FK → Account
├── deal_id FK → Deal (nullable, SET_NULL)
├── payment_transaction_id FK → PaymentTransaction (nullable, SET_NULL)
├── anomaly_type CharField(50)  # missing_payment, amount_mismatch, overpayment, status_mismatch
├── severity CharField(20)  # high, medium, low
├── expected_amount DecimalField(max_digits=15, decimal_places=2, null=True)
├── actual_amount DecimalField(max_digits=15, decimal_places=2, null=True)
├── expected_status CharField(50, blank=True)
├── actual_status CharField(50, blank=True)
├── description TextField
└── timestamps

Resolution (CommonField)
├── identifier UUID PK
├── anomaly_id FK → Anomaly (unique, 1:1, CASCADE)
├── resolved_by FK → User (PROTECT)
├── resolution_type CharField(50)  # adjust_deal, refund, manual_review, ignore
├── notes TextField(blank=True)
├── resolved_at DateTimeField(default=now)
└── timestamps
```

**Relationships**:
- `ReconciliationRun` 1:M `Anomaly`
- `Anomaly` 1:1 `Resolution` (nullable until resolved)
- `Anomaly` M:1 `Deal` (nullable), `Anomaly` M:1 `PaymentTransaction` (nullable)

### Audit Models (`apps/audit/models.py`)

```
AuditLog (CommonField)
├── identifier UUID PK
├── account_id FK → Account (CASCADE)
├── user_id FK → User (nullable, SET_NULL)
├── action CharField(100)  # resolve_anomaly, sync_hubspot, create_payment, change_role, etc.
├── entity_type CharField(50)  # anomaly, deal, transaction, user, reconciliation_run
├── entity_id CharField(64)  # String to support UUIDs
├── old_values JSONField(null=True)
├── new_values JSONField(null=True)
├── ip_address GenericIPAddressField(null=True)
└── timestamps
```

---

## Roles & Permissions

### Roles

| Role | Description |
|---|---|
| `admin` | Full access: manage users, trigger syncs, resolve anomalies, view everything |
| `analyst` | Operational access: trigger sync, view all data, resolve anomalies, view audit |
| `viewer` | Read-only: view customers, deals, payments, anomalies, dashboard |

### Permissions

| # | Codename | Description | admin | analyst | viewer |
|---|----------|-------------|-------|---------|--------|
| 1 | `manage_users` | Create/deactivate/change roles | Yes | - | - |
| 2 | `trigger_sync` | Trigger all data syncs (HubSpot + Stripe) | Yes | Yes | - |
| 3 | `view_customers` | List/view customer data | Yes | Yes | Yes |
| 4 | `view_deals` | List/view deal data | Yes | Yes | Yes |
| 5 | `view_payments` | List/view payment transactions | Yes | Yes | Yes |
| 6 | `view_anomalies` | List/view anomaly records | Yes | Yes | Yes |
| 7 | `resolve_anomalies` | Mark anomalies as resolved | Yes | Yes | - |
| 8 | `run_reconciliation` | Trigger reconciliation engine | Yes | Yes | - |
| 9 | `view_audit_logs` | List/filter audit trail | Yes | Yes | - |
| 10 | `view_dashboard` | Access summary dashboard | Yes | Yes | Yes |

### DRF Permission Classes

```python
# apps/accounts/permissions.py
from rest_framework.permissions import BasePermission

class HasPermission(BasePermission):
    """
    Check that the user's account role has a specific permission codename.
    Usage: permission_classes = [HasPermission('resolve_anomalies')]
    """
    codename = None

    def __init__(self, codename=None):
        self.codename = codename

    def __call__(self):
        return self

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            account = request.user.account
        except Exception:
            return False
        if not account or not account.role:
            return False
        return account.role.permissions.filter(codename=self.codename).exists()


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.account.role.name == 'admin'
        except Exception:
            return False
```

---

## API Endpoints

### Auth (unauthenticated except `me`)
```
POST   /api/auth/register/          # Create user + account, return JWT
POST   /api/auth/login/             # Email + password → JWT access + refresh
POST   /api/auth/refresh/           # Refresh token → new access token
GET    /api/auth/me/                # Current user + account + role info
```

### CRM — HubSpot Data
```
GET    /api/crm/customers/           # List, search by email/name, filter by lifecycle_stage
GET    /api/crm/customers/{id}/      # Customer detail + deals summary
GET    /api/crm/deals/               # List, filter by stage, customer_id, amount range
GET    /api/crm/deals/{id}/          # Deal detail + payment summary (total paid, status)
POST   /api/crm/sync/contacts/       # Trigger Celery task: sync_hubspot_contacts
POST   /api/crm/sync/deals/          # Trigger Celery task: sync_hubspot_deals
```

### Payments (synced from Stripe, analogous to CRM sync)
```
POST   /api/payments/sync/            # Trigger Celery task: sync_stripe_payments
GET    /api/payments/                 # List synced transactions, filter by status/email/provider
GET    /api/payments/{id}/            # Detail + provider record + queue jobs
POST   /api/payments/webhook/stripe/  # Stripe webhook receiver (unauthenticated, signature verified)
POST   /api/payments/webhook/flutterwave/ # Flutterwave webhook (future)
GET    /api/payments/stats/           # Payment summary: total by status, provider breakdown
```

### Reconciliation
```
POST   /api/reconciliation/run/      # Trigger Celery task: run_reconciliation
GET    /api/reconciliation/runs/     # Run history with status and counts
GET    /api/reconciliation/runs/{id}/# Single run detail + anomalies found in that run
GET    /api/reconciliation/anomalies/# List/filter by type, severity, resolved status, date range
GET    /api/reconciliation/anomalies/{id}/ # Anomaly detail + resolution if exists
POST   /api/reconciliation/anomalies/{id}/resolve/ # { resolution_type, notes } → create resolution
GET    /api/reconciliation/dashboard/# Summary: anomaly counts by type/severity, recent anomalies, trend data
```

### Audit
```
GET    /api/audit/logs/              # Filter by action, entity_type, user_id, date range, account
```

### Admin (admin role only)
```
GET    /api/admin/users/             # List all users with roles
POST   /api/admin/users/             # Create new user + account
GET    /api/admin/users/{id}/        # User detail
PATCH  /api/admin/users/{id}/        # Change role, activate/deactivate
```

---

## Celery Tasks

| Task | Trigger | Purpose |
|------|---------|---------|
| `sync_hubspot_contacts` | Manual via API & scheduled (every 30 min) | Pull contacts from HubSpot, incremental upsert Customers |
| `sync_hubspot_deals` | Manual via API & scheduled (every 30 min) | Pull deals from HubSpot, incremental upsert Deals |
| `sync_stripe_payments` | Manual via API & scheduled (every 30 min) | Pull PaymentIntents from Stripe, upsert PaymentTransaction |
| `handle_stripe_webhook` | Stripe webhook event | Verify signature, upsert/update PaymentProviderRecord |
| `run_reconciliation` | After sync + after webhook + manual | Match deals to payments by email, sum amounts, create anomalies |
| `cleanup_old_jobs` | Daily via Celery Beat | Clean up completed QueueJobRecords older than 7 days |

### Task Flow

```
Seed Script (one-time):
  manage.py seed      → Creates contacts & deals in HubSpot sandbox (via API)
                      → Creates PaymentIntents in Stripe test mode (via API)
                      → Includes deliberate mismatches for anomalies
                      → Outputs summary: X contacts, Y deals, Z payments created

Sync Flow:
  POST /api/crm/sync/contacts/  → sync_hubspot_contacts task
                                → HubSpot API → upsert Customers
  POST /api/crm/sync/deals/     → sync_hubspot_deals task
                                → HubSpot API → upsert Deals
  POST /api/payments/sync/      → sync_stripe_payments task
                                → Stripe API → upsert PaymentTransactions
  (after all syncs complete)    → triggers run_reconciliation

Webhook Flow (real-time updates):
  Stripe sends                  → POST /api/payments/webhook/stripe/
                                → handle_stripe_webhook task
                                → upsert PaymentProviderRecord
                                → triggers run_reconciliation

Reconciliation Flow:
  run_reconciliation  → creates ReconciliationRun
                      → for each Deal: find matching PaymentTransactions
                        WHERE customer_email == deal.customer.email
                      → sum succeeded payments, compare to deal.amount
                      → create Anomaly records for mismatches
                      → update ReconciliationRun with counts
```

---

## HubSpot → Payments: How Matching Works

**HubSpot does NOT have foreign keys to payments/transactions.** HubSpot is a CRM that stores contacts, deals, and companies. It does not natively store payment data or have FK relationships to payment processors.

### Matching Strategy

1. **Email is the reconciliation key**: `PaymentTransaction.customer_email` (from Stripe's `receipt_email` on the PaymentIntent) must match `Customer.email` (from HubSpot contact). The reconciliation engine queries by email, not by FK.

2. **post-reconciliation FK linkage**: After the engine finds a match, it updates `PaymentTransaction.deal_id` and creates `Anomaly` records linking `deal_id` and `payment_transaction_id`. The FK exists for audit/display, but matching happens at reconcile time.

3. **Reconciliation logic** (from `apps/reconciliation/engine.py`):
```python
def reconcile(self, deal_qs):
    anomalies = []
    for deal in deal_qs:
        customer_email = deal.customer.email

        # Match payments by CUSTOMER EMAIL (not deal_id FK)
        payments = PaymentTransaction.objects.filter(
            customer_email=customer_email,
            status='succeeded'
        )

        if not payments.exists():
            anomalies.append(create_anomaly('missing_payment', deal=deal))
            continue

        # Auto-link matched payments to deal
        payments.update(deal_id=deal.id)

        total_paid = payments.aggregate(total=Sum('amount'))['total'] or 0

        if total_paid < deal.amount:
            anomalies.append(create_anomaly('amount_mismatch', deal=deal,
                                             expected=deal.amount, actual=total_paid))
        elif total_paid > deal.amount:
            anomalies.append(create_anomaly('overpayment', deal=deal,
                                             expected=deal.amount, actual=total_paid))
        elif deal.stage == 'closed_lost' and total_paid > 0:
            anomalies.append(create_anomaly('status_mismatch', deal=deal))
        # else: MATCH — no anomaly

    return anomalies
```

**Why email matching is necessary**: HubSpot and Stripe are separate SaaS systems. There is no cross-system foreign key. HubSpot doesn't know about Stripe payments, and Stripe doesn't know about HubSpot deals. The only shared identifier is the customer's email address. Our reconciliation engine bridges the gap.

### Seed Script (`manage.py seed`)

The seed script **replaces the e-commerce/LMS platform** by pre-populating both HubSpot and Stripe:

```
python manage.py seed [--account-id <uuid>]

Creates in HubSpot sandbox (via API):
  - 30 contacts with realistic names and emails (via Faker)
  - 20 deals associated to those contacts
    - 12 "closed_won" at matching amounts
    - 4 "negotiation" stage
    - 4 "closed_lost"

Creates in Stripe test mode (via API):
  - 20 PaymentIntents using test cards
  - 15 matched to deal emails with CORRECT amounts
  - 3 matched to deal emails with WRONG amounts (amount_mismatch)
  - 2 payments for emails that have NO HubSpot deal (orphan_payment)

Leaves 5 deals with NO payment (missing_payment anomaly)
Leaves 2 closed_lost deals that DO have payments (status_mismatch)

Expected reconciliation result after full sync:
  - 12 clean matches
  - 5 missing_payment anomalies
  - 3 amount_mismatch anomalies
  - 2 orphan_payment anomalies
  - 2 status_mismatch anomalies
```

---

## Environment Variables

```
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DATABASE_URL=postgres://user:pass@db:5432/dbname
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
HUBSPOT_ACCESS_TOKEN=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
JWT_SECRET=
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Implementation Phases

| Phase | Name | Files | Key Deliverable |
|-------|------|-------|-----------------|
| 1 | Scaffold & Docker | ~15 | `docker-compose up` → Django welcome page |
| 2 | Accounts & RBAC | ~10 | Register → JWT → protected endpoints with permission checks |
| 3 | CRM Module (HubSpot) | ~11 | `POST /api/crm/sync/` → data flows from HubSpot to local DB; `seed` command |
| 4 | Payments Module (Stripe) | ~12 | `POST /api/payments/sync/` → Celery → Stripe API → upserts PaymentTransactions |
| 5 | Reconciliation Engine | ~10 | Trigger reconciliation → anomalies surface on dashboard endpoint |
| 6 | Audit Logging | ~5 | All actions logged, filterable via `/api/audit/logs/` |
| 7 | Testing | ~12 | Full test coverage, documented TEST_PLAN.md |
| 8 | React Frontend | ~18 | Anomaly dashboard, payment tables, sync controls, login page |

**Total: ~90 files**

---

## docker-compose.yml

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: reconciliation_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  celery_worker:
    build: .
    command: celery -A config worker -l info -Q default,payments,reconciliation
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

  celery_beat:
    build: .
    command: celery -A config beat -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

volumes:
  pgdata:
```

---

## Testing Strategy (maps to ICC NFR6)

### Unit Tests
| Test File | Covers |
|-----------|--------|
| `accounts/tests/test_models.py` | User, Account, Role, Permission creation & constraints |
| `accounts/tests/test_auth.py` | Register → JWT, login, permission checks on endpoints |
| `crm/tests/test_models.py` | Customer, Deal constraints, FK integrity |
| `crm/tests/test_sync.py` | HubSpot sync logic (mocked API responses) |
| `payments/tests/test_models.py` | PaymentTransaction state machine (status transitions) |
| `payments/tests/test_stripe.py` | Stripe client (mocked), webhook signature verification |
| `reconciliation/tests/test_engine.py` | All 4 anomaly types, edge cases (null amounts, zero, duplicate emails) |
| `reconciliation/tests/test_api.py` | Anomaly resolve flow, dashboard aggregation accuracy |
| `audit/tests/test_logging.py` | AuditLog creation on key actions, filter queries |

### Integration Tests
- Full sync → payment → webhook → reconciliation pipeline
- Role permission enforcement across endpoints
- Celery task chaining (sync → reconciliation)

### Regression Tests
- Smoke tests for all GET endpoints
- CRUD verification for all write endpoints
- Documented in `TEST_PLAN.md`
