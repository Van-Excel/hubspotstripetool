import pytest
from django.contrib.auth import get_user_model
from apps.accounts.models import Account, Role
from apps.crm.models import Customer, Deal, HubspotOwner
from apps.payments.models import PaymentTransaction
from apps.reconciliation.models import ReconciliationRun, Anomaly, Resolution

User = get_user_model()


@pytest.fixture
def account(db):
    role = Role.objects.get(name="admin")
    user = User.objects.create_user(
        email="rec@test.local", password="test", first_name="Recon", last_name="Test"
    )
    return Account.objects.create(user=user, role=role)


@pytest.fixture
def customer(db, account):
    return Customer.objects.create(
        account=account, hubspot_contact_id="c1", email="john@example.com",
        first_name="John", last_name="Doe",
    )


@pytest.fixture
def deal_closedwon(db, account, customer):
    return Deal.objects.create(
        account=account, customer=customer, hubspot_deal_id="d1",
        deal_name="Deal Won", amount=500.00, stage="closedwon",
    )


@pytest.fixture
def deal_closedlost(db, account, customer):
    return Deal.objects.create(
        account=account, customer=customer, hubspot_deal_id="d2",
        deal_name="Deal Lost", amount=300.00, stage="closedlost",
    )


@pytest.fixture
def deal_negotiation(db, account, customer):
    return Deal.objects.create(
        account=account, customer=customer, hubspot_deal_id="d3",
        deal_name="Deal Negotiation", amount=200.00, stage="negotiation",
    )


@pytest.fixture
def payment(db, account, deal_closedwon):
    return PaymentTransaction.objects.create(
        account=account, deal=deal_closedwon, customer_email="john@example.com",
        amount=500.00, provider="stripe", status="succeeded",
        stripe_payment_intent_id="pi_match",
    )
