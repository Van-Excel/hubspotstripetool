import os
import json
import requests
import random
import time
from django.core.management.base import BaseCommand

HUBSPOT_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
BASE_URL = "https://api.hubapi.com"
HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json",
}

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
    "Daniel", "Lisa", "Matthew", "Nancy", "Anthony", "Betty", "Mark",
    "Margaret", "Donald", "Sandra",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
]

STAGES = [
    "closedwon", "closedwon", "closedwon", "contractsent", "closedlost",
    "closedwon", "closedlost", "closedwon", "decisionmakerboughtin", "closedlost",
]

AMOUNTS = [150, 250, 500, 750, 1200, 2000, 3500, 5000, 7500, 10000]


def _post(path, data, label=""):
    try:
        resp = requests.post(
            f"{BASE_URL}{path}", json=data, headers=HEADERS, timeout=30
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            body = e.response.json()
            msg = body.get("message", json.dumps(body))
            if "already exists" in msg or "409" in str(e.response.status_code):
                return None
        except Exception:
            msg = e.response.text[:300]
        raise RuntimeError(f"HTTP {e.response.status_code}: {msg}") from e


def _get(path, params=None):
    try:
        resp = requests.get(f"{BASE_URL}{path}", params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            body = e.response.json()
            msg = body.get("message", json.dumps(body))
        except Exception:
            msg = e.response.text[:300]
        raise RuntimeError(f"HTTP {e.response.status_code}: {msg}") from e


def _get_existing_contacts():
    contacts = []
    after = None
    while True:
        params = {"limit": 100, "properties": "email,firstname,lastname"}
        if after:
            params["after"] = after
        resp = requests.get(
            f"{BASE_URL}/crm/v3/objects/contacts",
            params=params,
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        contacts.extend(data.get("results", []))
        after = (data.get("paging") or {}).get("next", {}).get("after")
        if not after:
            break
    return contacts


class Command(BaseCommand):
    help = "Seed HubSpot sandbox with test contacts and deals"

    def add_arguments(self, parser):
        parser.add_argument("--contacts", type=int, default=20)
        parser.add_argument("--deals", type=int, default=15)

    def handle(self, *args, **options):
        if not HUBSPOT_TOKEN or len(HUBSPOT_TOKEN) < 10:
            self.stderr.write("HUBSPOT_ACCESS_TOKEN not set. Cannot seed.")
            return

        num_contacts = options["contacts"]
        num_deals = options["deals"]
        rng = random.Random(42)

        self.stdout.write(f"Seeding {num_contacts} contacts...")
        contact_ids = []
        contact_emails = []
        for i in range(num_contacts):
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            email = f"{first.lower()}.{last.lower()}{i}@example.com"
            data = {
                "properties": {
                    "email": email,
                    "firstname": first,
                    "lastname": last,
                }
            }
            try:
                result = _post("/crm/v3/objects/contacts", data, label=email)
                contact_ids.append(result["id"])
                contact_emails.append(email)
                self.stdout.write(f"  [{i+1}/{num_contacts}] {email}")
                time.sleep(0.12)
            except RuntimeError as e:
                msg = str(e)
                if "already exists" in msg.lower() or "409" in msg:
                    self.stdout.write(f"  [{i+1}/{num_contacts}] {email} (exists)")
                    # Will be picked up by fallback below
                else:
                    self.stderr.write(f"  [{i+1}/{num_contacts}] FAILED {email} — {e}")
                time.sleep(0.5)

        if not contact_ids:
            self.stdout.write("No new contacts created. Fetching existing contacts...")
            try:
                existing = _get_existing_contacts()
                for c in existing:
                    props = c.get("properties", {})
                    contact_ids.append(c["id"])
                    contact_emails.append(props.get("email", ""))
                self.stdout.write(f"Found {len(contact_ids)} existing contacts.")
            except RuntimeError as e:
                self.stderr.write(f"Failed to fetch existing contacts: {e}")
                return
            except RuntimeError as e:
                self.stderr.write(f"  [{i+1}/{num_contacts}] FAILED {email} — {e}")
                time.sleep(1)

        if not contact_ids:
            self.stderr.write("No contacts created. Check token and scopes. Aborting deals.")
            return

        self.stdout.write(f"\nSeeding {num_deals} deals...")
        for i in range(num_deals):
            idx = i % len(contact_ids)
            contact_id = contact_ids[idx]
            email = contact_emails[idx]
            amount = rng.choice(AMOUNTS)
            stage = rng.choice(STAGES)
            properties = {
                "dealname": f"Deal #{i+1:03d} — {email}",
                "amount": str(amount),
                "dealstage": stage,
            }
            if stage == "closedwon":
                properties["closedate"] = "2025-12-15T00:00:00Z"
            try:
                result = _post("/crm/v3/objects/deals", {"properties": properties}, label=f"deal#{i+1}")
                self._associate(result["id"], contact_id)
                self.stdout.write(f"  [{i+1}/{num_deals}] ${amount} {stage} -> {email}")
                time.sleep(0.12)
            except RuntimeError as e:
                self.stderr.write(f"  [{i+1}/{num_deals}] FAILED — {e}")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! {len(contact_ids)} contacts, {num_deals} deals attempted."
        ))

    def _associate(self, deal_id, contact_id):
        url = f"{BASE_URL}/crm/v3/objects/deals/{deal_id}/associations/contacts/{contact_id}/3"
        resp = requests.put(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
