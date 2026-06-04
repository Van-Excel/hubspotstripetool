"""
Standalone seed script — creates demo data in HubSpot + Stripe.
No Django, no database, pure HTTP. Reads tokens from .env.
Usage: python seed_demo.py
"""
import os
import json
import random
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_TOKEN = os.environ["HUBSPOT_ACCESS_TOKEN"].strip()
STRIPE_KEY = os.environ["STRIPE_SECRET_KEY"].strip()

HS_HEADERS = {"Authorization": f"Bearer {HUBSPOT_TOKEN}", "Content-Type": "application/json"}
HS_BASE = "https://api.hubapi.com/crm/v3"

# Stripe uses basic auth (secret_key:)
STRIPE_AUTH = base64.b64encode(f"{STRIPE_KEY}:".encode()).decode()
ST_HEADERS = {"Authorization": f"Basic {STRIPE_AUTH}", "Content-Type": "application/x-www-form-urlencoded"}
ST_BASE = "https://api.stripe.com/v1"

rng = random.Random(7)

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph",
    "Jessica", "Thomas", "Sarah", "Christopher", "Karen", "Daniel", "Lisa",
    "Matthew", "Nancy", "Anthony", "Betty", "Mark", "Margaret", "Donald", "Sandra",
    "Paul", "Kimberly", "Steven", "Michelle", "Andrew", "Amanda", "Kenneth", "Emily",
    "Joshua", "Dorothy", "Kevin", "Shirley", "Brian", "Angela", "George", "Helen",
    "Edward", "Deborah", "Ronald", "Ruth",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter",
]

AMOUNTS = [150, 250, 500, 750, 1200, 2000, 3500, 5000, 7500, 10000]

STAGES = [
    "closedwon", "closedwon", "closedwon", "contractsent", "closedlost",
    "closedwon", "closedlost", "closedwon", "decisionmakerboughtin", "closedlost",
]


def hs_post(path, data):
    resp = requests.post(f"{HS_BASE}{path}", json=data, headers=HS_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def hs_put(url):
    resp = requests.put(f"https://api.hubapi.com{url}", headers=HS_HEADERS, timeout=30)
    resp.raise_for_status()


def st_post(path, data):
    resp = requests.post(f"{ST_BASE}{path}", data=data, headers=ST_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


print("=== Phase 1: Creating HubSpot Contacts ===")
contact_ids = []
contact_emails = []

for i in range(80):
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    email = f"{first.lower()}.{last.lower()}{i}@iccdemo.com"
    data = {"properties": {"email": email, "firstname": first, "lastname": last}}
    try:
        result = hs_post("/objects/contacts", data)
        contact_ids.append(result["id"])
        contact_emails.append(email)
        print(f"  [{i+1:3d}/80] {email}")
        time.sleep(0.08)
    except Exception as e:
        print(f"  [{i+1:3d}/80] FAILED {email}: {e}")
        time.sleep(0.5)

print(f"\nCreated {len(contact_ids)} contacts.\n")

print("=== Phase 2: Creating HubSpot Deals ===")
deal_amounts = {}
deal_stages = {}
deal_emails = {}

for i in range(50):
    idx = i % len(contact_ids)
    contact_id = contact_ids[idx]
    email = contact_emails[idx]
    amount = rng.choice(AMOUNTS)
    stage = rng.choice(STAGES)

    props = {
        "dealname": f"Course Enrollment #{i+1:03d} — {email}",
        "amount": str(amount),
        "dealstage": stage,
    }
    if stage == "closedwon":
        props["closedate"] = "2025-12-15T00:00:00Z"

    try:
        result = hs_post("/objects/deals", {"properties": props})
        url = f"/crm/v3/objects/deals/{result['id']}/associations/contacts/{contact_id}/3"
        hs_put(url)
        deal_amounts[i] = amount
        deal_stages[i] = stage
        deal_emails[i] = email
        print(f"  [{i+1:2d}/50] ${amount:>6} {stage:>20} -> {email}")
        time.sleep(0.08)
    except Exception as e:
        print(f"  [{i+1:2d}/50] FAILED: {e}")
        time.sleep(0.5)

print(f"\nCreated 50 deals.\n")

print("=== Phase 3: Creating Stripe PaymentIntents ===")
payments = 0
mismatches = 0
skipped = 0

for i in range(50):
    if i % 5 == 3:
        skipped += 1
        continue

    email = deal_emails.get(i, "")
    amount = deal_amounts.get(i, 0)
    if not email or amount <= 0:
        continue

    payment_amount = int(amount * 100)
    scenario = "match"

    if i % 5 == 4:
        payment_amount = int(amount * rng.uniform(0.4, 0.8) * 100)
        scenario = "mismatch"

    try:
        st_post("/payment_intents", {
            "amount": str(payment_amount),
            "currency": "usd",
            "receipt_email": email,
            "confirm": "true",
            "payment_method": "pm_card_visa",
            "automatic_payment_methods[enabled]": "true",
            "automatic_payment_methods[allow_redirects]": "never",
            "metadata[deal_index]": str(i),
            "metadata[scenario]": scenario,
        })
        if scenario == "mismatch":
            mismatches += 1
            print(f"  [MISMATCH] ${payment_amount/100:.2f} -> {email}")
        else:
            payments += 1
            print(f"  [MATCH] ${payment_amount/100:.2f} -> {email}")
        time.sleep(0.12)
    except Exception as e:
        print(f"  FAILED: {e}")
        time.sleep(0.5)

print(f"\n=== Done! ===")
print(f"Contacts:    {len(contact_ids)}")
print(f"Deals:       50")
print(f"Payments:    {payments} match + {mismatches} mismatch")
print(f"Skipped:     {skipped} deals without payments (missing_payment anomaly)")
print(f"\nNext: trigger sync on deployed API")
print(f"  POST {os.environ.get('API_URL', 'https://your-cloud-run-url')}/api/crm/sync/")
print(f"  POST {os.environ.get('API_URL', 'https://your-cloud-run-url')}/api/payments/sync/")
print(f"  POST {os.environ.get('API_URL', 'https://your-cloud-run-url')}/api/reconciliation/run/")
