# Third-Party Integration Setup

Instructions for setting up the external APIs this project integrates with.

---

## 1. HubSpot CRM — Developer Sandbox

### Sign Up
1. Go to [developers.hubspot.com](https://developers.hubspot.com/)
2. Click **"Start free"** or **"Sign up"**
3. Create an account (free — no credit card required)
4. After sign-up, you'll have a **Developer Test Account** (isolated from real data)

### Create a Private App
1. In your HubSpot account, go to **Settings** (gear icon top-right)
2. Navigate to **Integrations → Private Apps**
3. Click **"Create private app"**
4. Name it: `Reconciliation Dashboard`
5. On the **Scopes** tab, add these scopes:
   - `crm.objects.contacts.read` — Read contacts
   - `crm.objects.contacts.write` — Write contacts (for seed script)
   - `crm.objects.deals.read` — Read deals
   - `crm.objects.deals.write` — Write deals (for seed script)
   - `crm.objects.owners.read` — Read owners
6. Click **"Create app"** at the top
7. Review and click **"Continue creating"**
8. **Copy the access token** — it only shows once!

### Configure
Add to `.env`:
```
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Verify
After setup and after Phase 3 is installed, run:
```bash
python manage.py sync_hubspot_contacts
```
Should return `200 OK` with contact data (empty or from seed).

---

## 2. Stripe — Test Mode

### Sign Up
1. Go to [dashboard.stripe.com/register](https://dashboard.stripe.com/register)
2. Create an account (free — no activation required for test mode)
3. Skip the activation prompts — test mode works immediately

### Enable Test Mode
1. In the Stripe Dashboard, check the toggle at the top right
2. Make sure **"Test mode"** is ON (orange badge)
3. You should see "Test mode" in the header

### Get API Keys
1. Go to **Developers → API Keys** (left sidebar)
2. Copy the **Secret key** — it starts with `sk_test_`

### Get Webhook Secret (Phase 4)
1. Go to **Developers → Webhooks**
2. Click **"Add endpoint"**
3. URL: `http://localhost:8000/api/payments/webhook/stripe/`
4. Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`
5. After creating, click **"Reveal"** on the Signing Secret

### Configure
Add to `.env`:
```
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxx
```

### Verify
After setup and after Phase 4 is installed:
```bash
python manage.py sync_stripe_payments
```

---

## 3. Test Cards (for Seed Script / Manual Testing)

Use these test card numbers in Stripe test mode:

| Scenario | Card Number |
|----------|------------|
| Successful payment | `4242 4242 4242 4242` |
| Declined | `4000 0000 0000 0002` |
| Requires 3D Secure | `4000 0027 6000 3184` |

- Expiry: Any future date (e.g. `12/30`)
- CVC: Any 3 digits (e.g. `123`)

---

## 4. Check Integration Status

After all phases are installed:
```bash
python manage.py seed          # Creates test data in HubSpot + Stripe
python manage.py sync_all      # Synces from both providers
python manage.py reconcile     # Runs reconciliation engine
```

Then visit the dashboard to see anomalies.
