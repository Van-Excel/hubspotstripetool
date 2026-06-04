from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import Account
from apps.crm.services.hubspot_client import HubSpotClient
from apps.crm.services.sync import sync_owners, sync_contacts, sync_deals
from apps.payments.models import PaymentTransaction, PaymentProviderRecord
from apps.reconciliation.engine import ReconciliationEngine
import stripe


class Command(BaseCommand):
    help = "Sync all data from HubSpot and Stripe, then run reconciliation"

    def handle(self, *args, **options):
        import os
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

        account = Account.objects.first()
        if not account:
            self.stderr.write("No account. Run migrations first.")
            return

        client = HubSpotClient()

        self.stdout.write("1/5 Syncing HubSpot owners...")
        sync_owners(account, client)

        self.stdout.write("2/5 Syncing HubSpot contacts...")
        sync_contacts(account, client)

        self.stdout.write("3/5 Syncing HubSpot deals...")
        sync_deals(account, client)

        self.stdout.write("4/5 Syncing Stripe payments...")
        imported = 0
        try:
            for pi in stripe.PaymentIntent.list(limit=100).auto_paging_iter():
                pi_id = pi.id
                email = pi.receipt_email or ""
                amount = float(pi.amount) / 100
                status = "succeeded" if pi.status == "succeeded" else "failed"

                tx, created = PaymentTransaction.objects.update_or_create(
                    stripe_payment_intent_id=pi_id,
                    defaults={
                        "account": account,
                        "customer_email": email,
                        "amount": amount,
                        "currency": pi.currency or "usd",
                        "provider": "stripe",
                        "status": status,
                        "raw_data": pi.to_dict() if hasattr(pi, 'to_dict') else {},
                        "synced_at": timezone.now(),
                    },
                )
                PaymentProviderRecord.objects.update_or_create(
                    transaction=tx,
                    defaults={
                        "provider_payment_id": pi_id,
                        "provider_status": pi.status,
                        "amount_charged": amount,
                        "webhook_received_at": timezone.now(),
                    },
                )
                imported += 1
        except Exception as e:
            import traceback
            self.stderr.write(f"  Stripe sync error: {e}\n{traceback.format_exc()}")

        self.stdout.write(f"  Imported {imported} payment(s)")

        self.stdout.write("5/5 Running reconciliation...")
        engine = ReconciliationEngine()
        run = engine.run(account)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone!"
                f"\n  Deals processed: {run.deals_processed}"
                f"\n  Anomalies found: {run.anomalies_found}"
            )
        )
        if run.anomalies_found > 0:
            for a in run.anomalies.all():
                self.stdout.write(f"  [{a.anomaly_type}] {a.severity} — {a.description[:120]}")
