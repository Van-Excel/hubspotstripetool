import pytest
from apps.payments.models import PaymentTransaction, PaymentProviderRecord, QueueJobRecord


@pytest.fixture
def account(db):
    from django.contrib.auth import get_user_model
    from apps.accounts.models import Account, Role
    User = get_user_model()
    role = Role.objects.get(name="admin")
    user = User.objects.create_user(
        email="paytest@example.com", password="test", first_name="Test", last_name="User"
    )
    return Account.objects.create(user=user, role=role)


@pytest.fixture
def transaction(db, account):
    return PaymentTransaction.objects.create(
        account=account,
        customer_email="john@example.com",
        amount=500.00,
        provider="stripe",
        status="succeeded",
        stripe_payment_intent_id="pi_test_123",
    )


class TestPaymentTransaction:
    def test_create_transaction(self, db, account):
        tx = PaymentTransaction.objects.create(
            account=account,
            customer_email="test@example.com",
            amount=250.00,
            provider="stripe",
            status="pending",
            stripe_payment_intent_id="pi_test_456",
        )
        assert tx.customer_email == "test@example.com"
        assert tx.amount == 250.00
        assert tx.status == "pending"
        assert tx.identifier is not None

    def test_deal_nullable(self, db, account):
        tx = PaymentTransaction.objects.create(
            account=account,
            customer_email="test@example.com",
            amount=100.00,
            provider="stripe",
            status="succeeded",
            stripe_payment_intent_id="pi_nullable",
        )
        assert tx.deal is None

    def test_unique_payment_intent(self, db, account):
        PaymentTransaction.objects.create(
            account=account,
            customer_email="a@b.com",
            amount=10,
            provider="stripe",
            status="succeeded",
            stripe_payment_intent_id="pi_unique",
        )
        with pytest.raises(Exception):
            PaymentTransaction.objects.create(
                account=account,
                customer_email="b@c.com",
                amount=20,
                provider="stripe",
                status="succeeded",
                stripe_payment_intent_id="pi_unique",
            )

    def test_status_choices(self, db, account):
        for status in ["pending", "processing", "succeeded", "failed", "refunded"]:
            tx = PaymentTransaction.objects.create(
                account=account,
                customer_email=f"{status}@test.com",
                amount=10,
                provider="stripe",
                status=status,
                stripe_payment_intent_id=f"pi_{status}",
            )
            assert tx.status == status


class TestPaymentProviderRecord:
    def test_one_to_one_transaction(self, db, transaction):
        record = PaymentProviderRecord.objects.create(
            transaction=transaction,
            provider_payment_id="pi_123",
            provider_status="succeeded",
            amount_charged=500.00,
        )
        assert record.transaction == transaction
        with pytest.raises(Exception):
            PaymentProviderRecord.objects.create(
                transaction=transaction,
                provider_payment_id="pi_456",
                provider_status="failed",
            )

    def test_create_record(self, db, transaction):
        record = PaymentProviderRecord.objects.create(
            transaction=transaction,
            provider_payment_id="pi_789",
            provider_status="succeeded",
            amount_charged=499.99,
            fee_amount=14.50,
        )
        assert record.amount_charged == 499.99
        assert record.fee_amount == 14.50


class TestQueueJobRecord:
    def test_create_job(self, db, transaction):
        job = QueueJobRecord.objects.create(
            transaction=transaction,
            status="queued",
        )
        assert job.status == "queued"
        assert job.retry_count == 0

    def test_multiple_jobs_per_transaction(self, db, transaction):
        QueueJobRecord.objects.create(transaction=transaction, status="queued")
        QueueJobRecord.objects.create(transaction=transaction, status="failed", retry_count=1)
        QueueJobRecord.objects.create(transaction=transaction, status="done", retry_count=0)
        assert transaction.queue_jobs.count() == 3
