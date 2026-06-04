import logging
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from apps.crm.models import Deal, Customer
from apps.payments.models import PaymentTransaction
from apps.reconciliation.models import ReconciliationRun, Anomaly

logger = logging.getLogger(__name__)


class ReconciliationEngine:
    def run(self, account) -> ReconciliationRun:
        run = ReconciliationRun.objects.create(
            account=account,
            status="running",
            started_at=timezone.now(),
            triggered_by="manual",
        )

        try:
            deals = Deal.objects.filter(
                account=account, is_deleted=False
            ).select_related("customer")

            run.deals_processed = deals.count()
            anomalies = []

            for deal in deals:
                deal_anomalies = self._check_deal(deal, run)
                anomalies.extend(deal_anomalies)

            run.anomalies_found = len(anomalies)
            run.status = "completed"

        except Exception as e:
            logger.exception("Reconciliation failed: %s", e)
            run.status = "failed"
            run.error_message = str(e)

        run.ended_at = timezone.now()
        run.save(update_fields=[
            "status", "deals_processed", "transactions_processed",
            "anomalies_found", "ended_at", "error_message", "updated",
        ])

        return run

    def _check_deal(self, deal: Deal, run: ReconciliationRun) -> list[Anomaly]:
        anomalies = []

        customer_email = deal.customer.email if deal.customer else ""

        payments = PaymentTransaction.objects.filter(
            customer_email=customer_email,
            status="succeeded",
        )
        run.transactions_processed = (run.transactions_processed or 0) + payments.count()

        if not payments.exists():
            anomaly = self._create_anomaly(
                run=run,
                deal=deal,
                anomaly_type="missing_payment",
                severity="high",
                description=f"No payments found for deal '{deal.deal_name}' (customer: {customer_email})",
                expected_amount=deal.amount,
                actual_amount=Decimal("0.00"),
            )
            anomalies.append(anomaly)
            return anomalies

        self._link_payments_to_deal(payments, deal)
        total_paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        if total_paid > deal.amount:
            anomaly = self._create_anomaly(
                run=run,
                deal=deal,
                anomaly_type="overpayment",
                severity="high",
                description=f"Total payments (${total_paid}) exceed deal amount (${deal.amount})",
                expected_amount=deal.amount,
                actual_amount=total_paid,
            )
            anomalies.append(anomaly)

        elif total_paid < deal.amount:
            diff = deal.amount - total_paid
            anomaly = self._create_anomaly(
                run=run,
                deal=deal,
                anomaly_type="amount_mismatch",
                severity="high",
                description=f"Total payments (${total_paid}) less than deal amount (${deal.amount}). Missing ${diff}.",
                expected_amount=deal.amount,
                actual_amount=total_paid,
            )
            anomalies.append(anomaly)

        elif deal.stage == "closedlost":
            anomaly = self._create_anomaly(
                run=run,
                deal=deal,
                anomaly_type="status_mismatch",
                severity="medium",
                description=f"Deal is closed_lost but payment of ${total_paid} exists",
                expected_status="closed_won",
                actual_status=deal.stage,
                expected_amount=deal.amount,
                actual_amount=total_paid,
            )
            anomalies.append(anomaly)

        else:
            logger.info(f"Deal {deal.deal_name} reconciled: ${deal.amount} = ${total_paid}  OK")

        for anomaly in anomalies:
            first_payment = payments.first()
            if first_payment and not anomaly.payment_transaction:
                anomaly.payment_transaction = first_payment
                anomaly.save(update_fields=["payment_transaction"])

        return anomalies

    def _link_payments_to_deal(self, payments, deal: Deal):
        unlinked = payments.filter(deal__isnull=True)
        updated = unlinked.update(deal=deal)
        if updated:
            logger.info(f"Linked {updated} payments to deal {deal.deal_name}")

    def _create_anomaly(self, run, deal, anomaly_type, severity, description,
                        expected_amount=None, actual_amount=None,
                        expected_status=None, actual_status=None) -> Anomaly:
        return Anomaly.objects.create(
            reconciliation_run=run,
            account=run.account,
            deal=deal,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            expected_amount=expected_amount,
            actual_amount=actual_amount,
            expected_status=expected_status or "",
            actual_status=actual_status or "",
        )
