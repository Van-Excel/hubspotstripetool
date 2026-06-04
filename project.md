# Unified Commerce Reconciliation Dashboard

A Django REST Framework backend + React frontend that monitors payment workflows across HubSpot CRM and Stripe, reconciles transactions, and flags anomalies — built for an ICC Application Support Consultant role application.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x + Django REST Framework |
| Auth | `djangorestframework-simplejwt` (JWT) |
| Async Tasks | Celery + Redis |
| Database | PostgreSQL 16 |
| Payments | Stripe (Flutterwave-ready via provider interface) |
| CRM | HubSpot Private App API |
| Frontend | React 19 + TypeScript + Vite |
| Styling | Tailwind CSS + shadcn/ui |
| State | TanStack Query v5 |
| Containerization | Docker + docker-compose |

---

## Quick Start

### 1. Setup API Keys

Get tokens from:
- **HubSpot**: [developers.hubspot.com](https://developers.hubspot.com) → Private App (scopes: `crm.objects.contacts.read/write`, `crm.objects.deals.read/write`, `crm.objects.owners.read`)
- **Stripe**: [dashboard.stripe.com](https://dashboard.stripe.com) → Test mode → API Keys → Secret key (`sk_test_...`)

Add to `.env`:
```
HUBSPOT_ACCESS_TOKEN=pat-...
STRIPE_SECRET_KEY=sk_test_...
```

### 2. Run Backend

```bash
# Option A: Docker
docker-compose up --build

# Option B: Local
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py runserver
```

### 3. Seed Demo Data

```bash
python manage.py seed_hubspot --contacts 20 --deals 15   # Populate HubSpot sandbox
python manage.py seed_stripe                               # Populate Stripe test mode
python manage.py sync_all                                  # Sync all + reconcile
```

### 4. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173)

---

## Login Credentials

| Email | Password | Role |
|---|---|---|
| `admin@reconciliation.local` | `admin123` | admin |

New users register via the backend API at `POST /api/auth/register/` (default role: viewer).

---

## Architecture

### Backend Apps (~80 files, 73 tests)

| App | Models | Purpose |
|-----|--------|---------|
| `core` | `CommonField` | UUID v7 PK, timestamps, `old_id` on all models |
| `accounts` | `User`, `Account`, `Role`, `Permission` | JWT auth, RBAC (3 roles, 10 permissions) |
| `crm` | `Customer`, `Deal`, `HubspotOwner`, `SyncLog` | HubSpot API sync (contacts, deals, owners) |
| `payments` | `PaymentTransaction`, `ProviderRecord`, `QueueJob` | Stripe sync + webhook (Flutterwave-ready interface) |
| `reconciliation` | `ReconciliationRun`, `Anomaly`, `Resolution` | Core engine — 4 anomaly types |
| `audit` | `AuditLog` | All user actions logged |

### API Endpoints (24)

```
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/refresh/
GET    /api/auth/me/
GET    /api/admin/users/
PATCH  /api/admin/users/{id}/

GET    /api/crm/customers/
GET    /api/crm/deals/
POST   /api/crm/sync/

GET    /api/payments/
POST   /api/payments/sync/
POST   /api/payments/webhook/stripe/
GET    /api/payments/stats/

POST   /api/reconciliation/run/
GET    /api/reconciliation/runs/
GET    /api/reconciliation/anomalies/
POST   /api/reconciliation/anomalies/{id}/resolve/
GET    /api/reconciliation/dashboard/

GET    /api/audit/logs/
```

### Frontend Pages (8)

| Route | Permissions | Page |
|---|---|---|
| `/login` | public | Login form |
| `/dashboard` | `view_dashboard` | Stat cards, anomaly breakdown, recent anomalies table |
| `/anomalies` | `view_anomalies` | Filterable table + resolve dialog |
| `/payments` | `view_payments` | Payment list with status filter |
| `/deals` | `view_deals` | Deal list with stage filter |
| `/customers` | `view_customers` | Customer list |
| `/audit` | `view_audit_logs` | Audit trail |
| `/admin/users` | `manage_users` | User management (role changes) |

### Roles & Permissions

| Role | Permissions |
|---|---|
| **admin** | All 10 permissions |
| **analyst** | trigger_sync, view_*, resolve_anomalies, run_reconciliation, view_audit_logs |
| **viewer** | view_customers, view_deals, view_payments, view_anomalies, view_dashboard |

### Reconciliation Engine

Detects 4 anomaly types:
1. **missing_payment** — Deal exists, no payment found for customer email
2. **amount_mismatch** — Total payments < deal amount
3. **overpayment** — Total payments > deal amount  
4. **status_mismatch** — Deal closed_lost but payment exists

Matching key: `customer_email` (HubSpot contacts ↔ Stripe PaymentIntent receipt_email)

### Data Flow

```
Seed Script (simulates e-commerce)
  → Creates deals in HubSpot sandbox
  → Creates confirmed PaymentIntents in Stripe test mode

Sync (pull from both sides)
  → sync_hubspot_* : API → Customer + Deal tables
  → sync_stripe_payments : API → PaymentTransaction table

Reconciliation (match by email)
  → For each Deal: sum succeeded payments for customer email
  → Compare to deal.amount → create Anomaly records

Dashboard
  → Analyst views anomalies, investigates, marks resolved
  → Actions logged to AuditLog
```

### Directory Structure

```
hubspotandstripetool/
├── config/                    # Django project settings, urls, celery
├── apps/
│   ├── core/                  # CommonField base model
│   ├── accounts/              # Auth, RBAC, user management
│   ├── crm/                   # HubSpot models, client, sync
│   ├── payments/              # Stripe models, client, sync
│   ├── reconciliation/        # Engine, anomalies, resolution
│   └── audit/                 # Audit logging
├── frontend/                  # React + TypeScript + Tailwind
│   └── src/
│       ├── providers/         # Auth context
│       ├── hooks/             # TanStack Query hooks
│       ├── components/        # UI, layout, anomaly-badge, stat-card
│       └── pages/             # Login, Dashboard, Anomalies, etc.
├── requirements/
├── docker-compose.yml
├── Dockerfile
├── plan.md                   # Full implementation plan
├── frontend.md               # Frontend design spec
├── integration.md            # Third-party API setup guide
├── cred.md                   # Test credentials
├── project.md                # This file
└── manage.py
```

---

## Commands Reference

```bash
python manage.py seed_hubspot --contacts 20 --deals 15    # Populate HubSpot
python manage.py seed_stripe                                # Populate Stripe
python manage.py sync_all                                   # Sync + Reconcile
python manage.py test                                       # Run tests (using pytest for better output)
python -m pytest apps/ -v                                   # Run all tests
```
