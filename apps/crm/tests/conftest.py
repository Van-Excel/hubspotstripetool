import pytest
from apps.accounts.models import Account, Role
from apps.crm.models import Customer, Deal, HubspotOwner, HubspotSyncLog


@pytest.fixture
def account(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    role = Role.objects.get(name="admin")
    user = User.objects.create_user(
        email="crmtest@example.com", password="test", first_name="Test", last_name="User"
    )
    return Account.objects.create(user=user, role=role)


@pytest.fixture
def owner(db, account):
    return HubspotOwner.objects.create(
        account=account,
        hubspot_owner_id="owner_123",
        email="owner@example.com",
        first_name="Sales",
        last_name="Owner",
    )


@pytest.fixture
def customer(db, account, owner):
    return Customer.objects.create(
        account=account,
        owner=owner,
        hubspot_contact_id="contact_456",
        email="john@example.com",
        first_name="John",
        last_name="Doe",
    )


@pytest.fixture
def deal(db, account, customer, owner):
    return Deal.objects.create(
        account=account,
        customer=customer,
        owner=owner,
        hubspot_deal_id="deal_789",
        deal_name="Test Deal",
        amount=500.00,
        stage="closedwon",
    )
