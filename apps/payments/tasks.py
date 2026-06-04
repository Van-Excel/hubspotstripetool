import logging
from django.utils import timezone
from celery import shared_task

from apps.payments.models import PaymentTransaction, PaymentProviderRecord, QueueJobRecord
from apps.payments.services.stripe_client import StripeClient
from apps.accounts.models import Account

logger = logging.getLogger(__name__)

STATUS_MAP = {
    "succeeded": "succeeded",
    "processing": "processing",
    "requires_payment_method": "failed",
    "requires_confirmation": "pending",
    "requires_action": "processing",
    "canceled": "failed",
}


def _get_first_account():
    return Account.objects.select_related("user").first()


def _extract_email(payment_intent) -> str:
    try:
        receipt_email = payment_intent.receipt_email
        if receipt_email:
            return receipt_email
        metadata = getattr(payment_intent, "metadata", {}) or {}
        return metadata.get("email", "")
    except Exception:
        return ""


@shared_task(name="sync_stripe_payments")
def sync_stripe_payments():
    account = _get_first_account()
    if not account:
        return {"error": "No account found"}

    client = StripeClient()
    created = updated = 0
    try:
        for pi in client.get_all_payments():
            pi_id = getattr(pi, "id", "")
            if not pi_id:
                continue
            email = _extract_email(pi)
            amount = float(getattr(pi, "amount", 0)) / 100
            currency = getattr(pi, "currency", "usd")
            stripe_status = getattr(pi, "status", "")
            our_status = STATUS_MAP.get(stripe_status, "pending")

            defaults = {
                "account": account,
                "customer_email": email,
                "amount": amount,
                "currency": currency,
                "provider": "stripe",
                "status": our_status,
                "raw_data": pi.to_dict() if hasattr(pi, "to_dict") else {},
                "synced_at": timezone.now(),
            }
            if not PaymentTransaction.objects.filter(stripe_payment_intent_id=pi_id).exists():
                defaults["stripe_payment_intent_id"] = pi_id

            tx, was_created = PaymentTransaction.objects.update_or_create(
                stripe_payment_intent_id=pi_id,
                defaults=defaults,
            )

            PaymentProviderRecord.objects.update_or_create(
                transaction=tx,
                defaults={
                    "provider_payment_id": pi_id,
                    "provider_status": stripe_status,
                    "amount_charged": amount,
                    "webhook_received_at": timezone.now(),
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        logger.info(f"Stripe sync complete: {created} created, {updated} updated")

    except Exception as e:
        logger.exception("Stripe sync failed: %s", e)
        return {"error": str(e)}

    from apps.reconciliation.tasks import run_reconciliation
    run_reconciliation.delay()

    return {
        "status": "completed",
        "created": created,
        "updated": updated,
    }


@shared_task(name="handle_stripe_webhook")
def handle_stripe_webhook(event_data: dict):
    event_type = event_data.get("type", "")
    payload = event_data.get("data", {}).get("object", {})

    if event_type not in ("payment_intent.succeeded", "payment_intent.payment_failed"):
        return {"status": "ignored", "event": event_type}

    pi_id = payload.get("id", "")
    if not pi_id:
        return {"error": "No payment intent ID"}

    try:
        tx = PaymentTransaction.objects.get(stripe_payment_intent_id=pi_id)
    except PaymentTransaction.DoesNotExist:
        return {"error": f"PaymentIntent {pi_id} not found"}

    tx.status = STATUS_MAP.get(event_type, tx.status)
    tx.save(update_fields=["status", "updated"])

    PaymentProviderRecord.objects.update_or_create(
        transaction=tx,
        defaults={
            "provider_payment_id": pi_id,
            "provider_status": payload.get("status", ""),
            "amount_charged": (payload.get("amount", 0) / 100),
            "webhook_payload": payload,
            "webhook_received_at": timezone.now(),
        },
    )

    from apps.reconciliation.tasks import run_reconciliation
    run_reconciliation.delay()

    return {"status": "processed", "event": event_type}
