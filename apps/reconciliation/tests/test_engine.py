import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.crm.models import Deal
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.models import ReconciliationRun, Anomaly, Resolution
from apps.payments.models import PaymentTransaction

User = get_user_model()


class TestReconciliationEngine:
    def test_perfect_match(self, db, account, deal_closedwon, payment):
        engine = ReconciliationEngine()
        run = engine.run(account)
        assert run.status == "completed"
        assert run.anomalies_found == 0

    def test_missing_payment(self, db, account, deal_closedwon):
        engine = ReconciliationEngine()
        run = engine.run(account)
        assert run.anomalies_found == 1
        anomaly = run.anomalies.first()
        assert anomaly.anomaly_type == "missing_payment"
        assert anomaly.severity == "high"
        assert anomaly.expected_amount == deal_closedwon.amount

    def test_amount_mismatch_underpayment(self, db, account, deal_closedwon):
        PaymentTransaction.objects.create(
            account=account, customer_email="john@example.com",
            amount=300.00, provider="stripe", status="succeeded",
            stripe_payment_intent_id="pi_under",
        )
        engine = ReconciliationEngine()
        run = engine.run(account)
        assert run.anomalies_found == 1
        anomaly = run.anomalies.first()
        assert anomaly.anomaly_type == "amount_mismatch"
        assert anomaly.expected_amount == deal_closedwon.amount
        assert anomaly.actual_amount == Decimal("300.00")

    def test_overpayment(self, db, account, deal_closedwon):
        PaymentTransaction.objects.create(
            account=account, customer_email="john@example.com",
            amount=700.00, provider="stripe", status="succeeded",
            stripe_payment_intent_id="pi_over",
        )
        engine = ReconciliationEngine()
        run = engine.run(account)
        anomaly = run.anomalies.first()
        assert anomaly.anomaly_type == "overpayment"
        assert anomaly.actual_amount == Decimal("700.00")

    def test_status_mismatch_closed_lost_with_payment(self, db, account, deal_closedlost):
        PaymentTransaction.objects.create(
            account=account, customer_email="john@example.com",
            amount=300.00, provider="stripe", status="succeeded",
            stripe_payment_intent_id="pi_closedlost",
        )
        engine = ReconciliationEngine()
        run = engine.run(account)
        anomaly = run.anomalies.first()
        assert anomaly.anomaly_type == "status_mismatch"
        assert anomaly.expected_status == "closed_won"
        assert anomaly.actual_status == "closedlost"

    def test_multiple_payments_total_match(self, db, account, deal_closedwon):
        PaymentTransaction.objects.create(
            account=account, customer_email="john@example.com",
            amount=300.00, provider="stripe", status="succeeded",
            stripe_payment_intent_id="pi_a",
        )
        PaymentTransaction.objects.create(
            account=account, customer_email="john@example.com",
            amount=200.00, provider="stripe", status="succeeded",
            stripe_payment_intent_id="pi_b",
        )
        engine = ReconciliationEngine()
        run = engine.run(account)
        assert run.anomalies_found == 0

    def test_only_succeeded_payments_count(self, db, account, deal_closedwon):
        PaymentTransaction.objects.create(
            account=account, customer_email="john@example.com",
            amount=500.00, provider="stripe", status="failed",
            stripe_payment_intent_id="pi_failed",
        )
        engine = ReconciliationEngine()
        run = engine.run(account)
        assert run.anomalies_found == 1
        assert run.anomalies.first().anomaly_type == "missing_payment"

    def test_links_payments_to_deal(self, db, account, deal_closedwon):
        tx = PaymentTransaction.objects.create(
            account=account, customer_email="john@example.com",
            amount=500.00, provider="stripe", status="succeeded",
            stripe_payment_intent_id="pi_link",
        )
        engine = ReconciliationEngine()
        engine.run(account)
        tx.refresh_from_db()
        assert tx.deal == deal_closedwon

    def test_multiple_deals_same_customer(self, db, account, customer):
        deal1 = Deal.objects.create(
            account=account, customer=customer, hubspot_deal_id="dx1",
            deal_name="Deal 1", amount=300.00, stage="closedwon",
        )
        deal2 = Deal.objects.create(
            account=account, customer=customer, hubspot_deal_id="dx2",
            deal_name="Deal 2", amount=200.00, stage="closedwon",
        )
        PaymentTransaction.objects.create(
            account=account, customer_email="john@example.com",
            amount=300.00, status="succeeded", provider="stripe",
            stripe_payment_intent_id="pi_x1",
        )
        PaymentTransaction.objects.create(
            account=account, customer_email="john@example.com",
            amount=150.00, status="succeeded", provider="stripe",
            stripe_payment_intent_id="pi_x2",
        )
        engine = ReconciliationEngine()
        run = engine.run(account)
        assert run.anomalies_found >= 1


class TestReconciliationModels:
    def test_reconciliation_run_lifecycle(self, db, account):
        run = ReconciliationRun.objects.create(
            account=account, status="running",
        )
        assert run.status == "running"

    def test_anomaly_creation(self, db, account, deal_closedwon):
        run = ReconciliationRun.objects.create(account=account)
        anomaly = Anomaly.objects.create(
            reconciliation_run=run, account=account, deal=deal_closedwon,
            anomaly_type="amount_mismatch", severity="high",
            expected_amount=500.00, actual_amount=300.00,
            description="Test anomaly",
        )
        assert anomaly.anomaly_type == "amount_mismatch"
        assert anomaly.is_resolved is False

    def test_resolution(self, db, account, deal_closedwon):
        user = User.objects.first() or User.objects.create_user(
            email="resolver@test.com", password="test"
        )
        run = ReconciliationRun.objects.create(account=account)
        anomaly = Anomaly.objects.create(
            reconciliation_run=run, account=account, deal=deal_closedwon,
            anomaly_type="amount_mismatch", severity="high",
            expected_amount=500.00, actual_amount=300.00,
        )
        resolution = Resolution.objects.create(
            anomaly=anomaly, resolved_by=user,
            resolution_type="manual_review", notes="Looks fine.",
        )
        assert anomaly.is_resolved is True
        assert resolution.notes == "Looks fine."

    def test_resolution_one_to_one(self, db, account, deal_closedwon):
        user = User.objects.first() or User.objects.create_user(
            email="resolve2@test.com", password="test"
        )
        run = ReconciliationRun.objects.create(account=account)
        anomaly = Anomaly.objects.create(
            reconciliation_run=run, account=account, deal=deal_closedwon,
            anomaly_type="amount_mismatch", severity="medium",
        )
        Resolution.objects.create(
            anomaly=anomaly, resolved_by=user, resolution_type="ignore",
        )
        with pytest.raises(Exception):
            Resolution.objects.create(
                anomaly=anomaly, resolved_by=user, resolution_type="adjust_deal",
            )
