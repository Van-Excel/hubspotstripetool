import pytest
from apps.crm.models import Customer, Deal, HubspotOwner, HubspotSyncLog


class TestHubspotOwner:
    def test_create_owner(self, db, account):
        owner = HubspotOwner.objects.create(
            account=account,
            hubspot_owner_id="o_001",
            email="o1@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        assert str(owner) == "Jane Smith"
        assert owner.full_name == "Jane Smith"

    def test_unique_hubspot_owner_id(self, db, account):
        HubspotOwner.objects.create(account=account, hubspot_owner_id="o_001")
        with pytest.raises(Exception):
            HubspotOwner.objects.create(account=account, hubspot_owner_id="o_001")


class TestCustomer:
    def test_create_customer(self, db, account, owner):
        customer = Customer.objects.create(
            account=account,
            owner=owner,
            hubspot_contact_id="c_001",
            email="cust@example.com",
            first_name="John",
            last_name="Doe",
        )
        assert customer.full_name == "John Doe"
        assert str(customer) == "John Doe"

    def test_unique_hubspot_contact_id(self, db, account):
        Customer.objects.create(
            account=account, hubspot_contact_id="c_001", email="a@b.com"
        )
        with pytest.raises(Exception):
            Customer.objects.create(
                account=account, hubspot_contact_id="c_001", email="b@c.com"
            )

    def test_soft_delete(self, db, account, customer):
        customer.is_deleted = True
        customer.save()
        assert Customer.objects.filter(is_deleted=True).exists()

    def test_raw_properties_default(self, db, account, customer):
        assert isinstance(customer.raw_properties, dict)


class TestDeal:
    def test_create_deal(self, db, account, customer):
        deal = Deal.objects.create(
            account=account,
            customer=customer,
            hubspot_deal_id="d_001",
            deal_name="Big Sale",
            amount=1000.00,
            stage="negotiation",
        )
        assert "Big Sale" in str(deal)
        assert deal.amount == 1000.00
        assert deal.stage == "negotiation"

    def test_customer_cascade(self, db, account, customer, deal):
        customer.delete()
        assert not Deal.objects.filter(identifier=deal.identifier).exists()

    def test_unique_hubspot_deal_id(self, db, account, customer):
        Deal.objects.create(
            account=account,
            customer=customer,
            hubspot_deal_id="d_001",
            deal_name="Deal 1",
            amount=100,
            stage="closedwon",
        )
        with pytest.raises(Exception):
            Deal.objects.create(
                account=account,
                customer=customer,
                hubspot_deal_id="d_001",
                deal_name="Deal 2",
                amount=200,
                stage="closedlost",
            )

    def test_default_currency(self, db, account, customer, deal):
        assert deal.currency == "USD"

    def test_deal_customer_relationship(self, db, customer, deal):
        assert deal.customer == customer
        assert customer.deals.count() == 1

    def test_multiple_deals_per_customer(self, db, account, customer):
        Deal.objects.create(
            account=account,
            customer=customer,
            hubspot_deal_id="d_a",
            deal_name="Deal A",
            amount=300,
            stage="closedwon",
        )
        Deal.objects.create(
            account=account,
            customer=customer,
            hubspot_deal_id="d_b",
            deal_name="Deal B",
            amount=200,
            stage="negotiation",
        )
        assert Deal.objects.filter(customer=customer).count() == 2


class TestHubspotSyncLog:
    def test_create_sync_log(self, db, account):
        log = HubspotSyncLog.objects.create(
            account=account,
            entity_type="contact",
            records_created=10,
            records_updated=5,
            status="success",
        )
        assert log.status == "success"
        assert log.records_created == 10

    def test_sync_log_status_choices(self, db, account):
        for status in ["success", "partial", "failed", "running"]:
            log = HubspotSyncLog.objects.create(
                account=account,
                entity_type="deal",
                status=status,
            )
            assert log.status == status
