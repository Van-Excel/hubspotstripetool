import os
import random
import time
import requests
import stripe
from django.core.management.base import BaseCommand

HS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "").strip()
BASE = "https://api.hubapi.com"
HS_HEADERS = {"Authorization": f"Bearer {HS_TOKEN}", "Content-Type": "application/json"}


def _get_hubspot_deals():
    deals = []
    after = None
    while True:
        params = {"limit": 100, "properties": "dealname,amount,dealstage"}
        if after:
            params["after"] = after
        resp = requests.get(
            f"{BASE}/crm/v3/objects/deals", params=params, headers=HS_HEADERS, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        deals.extend(data.get("results", []))
        after = (data.get("paging") or {}).get("next", {}).get("after")
        if not after:
            break
    return deals


def _get_contact_email(deal_id):
    resp = requests.get(
        f"{BASE}/crm/v3/objects/deals/{deal_id}/associations/contacts",
        headers=HS_HEADERS, timeout=30,
    )
    resp.raise_for_status()
    assocs = resp.json().get("results", [])
    if not assocs:
        return None
    cid = assocs[0].get("toObjectId") or assocs[0].get("id")
    if not cid:
        return None
    cresp = requests.get(
        f"{BASE}/crm/v3/objects/contacts/{cid}?properties=email",
        headers=HS_HEADERS, timeout=30,
    )
    cresp.raise_for_status()
    return cresp.json().get("properties", {}).get("email")


class Command(BaseCommand):
    help = "Seed Stripe test mode with confirmed PaymentIntents matching HubSpot deals"

    def handle(self, *args, **options):
        if not STRIPE_KEY or len(STRIPE_KEY) < 10:
            self.stderr.write("STRIPE_SECRET_KEY not set. Aborting.")
            return
        if not HS_TOKEN or len(HS_TOKEN) < 10:
            self.stderr.write("HUBSPOT_ACCESS_TOKEN not set. Aborting.")
            return

        stripe.api_key = STRIPE_KEY.strip()
        rng = random.Random(42)

        self.stdout.write("Fetching HubSpot deals...")
        try:
            deals = _get_hubspot_deals()
        except Exception as e:
            self.stderr.write(f"Failed: {e}")
            return

        self.stdout.write(f"Found {len(deals)} deals")
        created = 0
        mismatches = 0
        skipped = 0

        for i, deal in enumerate(deals):
            props = deal.get("properties", {})
            amount = float(props.get("amount") or 0)
            deal_name = props.get("dealname", "")
            if amount <= 0:
                continue

            email = _get_contact_email(deal["id"])
            if not email:
                skipped += 1
                continue

            if i % 5 == 3:
                skipped += 1
                continue

            try:
                payment_amount = int(amount * 100)

                if i % 5 == 4:
                    payment_amount = int(amount * rng.uniform(0.4, 0.8) * 100)

                pi = stripe.PaymentIntent.create(
                    amount=payment_amount,
                    currency="usd",
                    receipt_email=email,
                    confirm=True,
                    payment_method="pm_card_visa",
                    automatic_payment_methods={
                        "enabled": True,
                        "allow_redirects": "never",
                    },
                    metadata={"deal_hubspot_id": deal["id"], "deal_name": deal_name},
                )

                if i % 5 == 4:
                    mismatches += 1
                    self.stdout.write(
                        f"  [MISMATCH] ${payment_amount/100:.2f} -> {email}"
                    )
                else:
                    created += 1
                    self.stdout.write(
                        f"  [MATCH] ${payment_amount/100:.2f} -> {email}"
                    )
                time.sleep(0.15)

            except stripe.error.CardError:
                created += 1
                self.stdout.write(f"  [MISMATCH via decline] ${amount} -> {email}")
            except stripe.error.StripeError as e:
                self.stderr.write(f"  FAILED {email}: {e}")
                time.sleep(0.5)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! {created} matching + {mismatches} mismatched payments created."
                f"\n{skipped} deals without payments -> missing_payment anomalies."
            )
        )
