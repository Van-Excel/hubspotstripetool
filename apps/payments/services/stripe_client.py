import os
import logging
from typing import Iterator
import stripe
from .base import BasePaymentProvider

logger = logging.getLogger(__name__)


class StripeClient(BasePaymentProvider):
    def __init__(self, secret_key: str | None = None):
        self.secret_key = secret_key or os.environ.get("STRIPE_SECRET_KEY", "").strip()
        stripe.api_key = self.secret_key

    def fetch_payments(self, limit: int = 100, starting_after: str | None = None) -> dict:
        params = {"limit": limit}
        if starting_after:
            params["starting_after"] = starting_after
        return stripe.PaymentIntent.list(**params)

    def get_all_payments(self) -> Iterator[dict]:
        starting_after = None
        while True:
            response = self.fetch_payments(limit=100, starting_after=starting_after)
            for pi in response.auto_paging_iter():
                yield pi
                starting_after = pi.get("id")
            if not response.get("has_more"):
                break

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        if not webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not set, skipping signature verification")
            return True
        try:
            stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return True
        except stripe.error.SignatureVerificationError:
            return False
        except ValueError:
            return False
