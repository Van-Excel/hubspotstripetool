import logging
from datetime import datetime
from django.db import transaction
from django.utils import timezone

from apps.crm.models import HubspotOwner, Customer, Deal, HubspotSyncLog
from apps.crm.services.hubspot_client import HubSpotClient

logger = logging.getLogger(__name__)


def parse_hubspot_date(value) -> datetime | None:
    if not value:
        return None
    try:
        return timezone.make_aware(
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        )
    except (ValueError, TypeError):
        return None


def sync_owners(account, client: HubSpotClient) -> HubspotSyncLog:
    log = HubspotSyncLog.objects.create(
        account=account,
        entity_type=HubspotSyncLog.EntityType.OWNER,
        status=HubspotSyncLog.SyncStatus.RUNNING,
        sync_started_at=timezone.now(),
    )
    try:
        owners = client.get_owners()
        for owner_data in owners:
            HubspotOwner.objects.update_or_create(
                hubspot_owner_id=str(owner_data["id"]),
                defaults={
                    "account": account,
                    "email": owner_data.get("email", ""),
                    "first_name": owner_data.get("firstName", ""),
                    "last_name": owner_data.get("lastName", ""),
                },
            )
        log.records_created = len(owners)
        log.status = HubspotSyncLog.SyncStatus.SUCCESS
    except Exception as e:
        logger.exception("Owner sync failed: %s", e)
        log.status = HubspotSyncLog.SyncStatus.FAILED
        log.error_message = str(e)
    log.sync_ended_at = timezone.now()
    log.save()
    return log


def sync_contacts(account, client: HubSpotClient) -> HubspotSyncLog:
    log = HubspotSyncLog.objects.create(
        account=account,
        entity_type=HubspotSyncLog.EntityType.CONTACT,
        status=HubspotSyncLog.SyncStatus.RUNNING,
        sync_started_at=timezone.now(),
    )
    created = updated = 0
    try:
        for contact in client.get_all_contacts():
            props = contact.get("properties", {})
            hubspot_id = str(contact["id"])
            email = props.get("email", "")
            owner_id = props.get("hubspot_owner_id")

            owner = None
            if owner_id:
                owner = HubspotOwner.objects.filter(
                    hubspot_owner_id=owner_id, account=account
                ).first()

            defaults = {
                "account": account,
                "owner": owner,
                "email": email,
                "first_name": props.get("firstname") or "",
                "last_name": props.get("lastname") or "",
                "phone": props.get("phone") or "",
                "lifecycle_stage": props.get("lifecyclestage") or "",
                "raw_properties": props,
                "synced_at": timezone.now(),
                "is_deleted": False,
            }
            obj, was_created = Customer.objects.update_or_create(
                hubspot_contact_id=hubspot_id,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        log.records_created = created
        log.records_updated = updated
        log.status = HubspotSyncLog.SyncStatus.SUCCESS
    except Exception as e:
        logger.exception("Contact sync failed: %s", e)
        log.status = HubspotSyncLog.SyncStatus.FAILED
        log.error_message = str(e)
    log.sync_ended_at = timezone.now()
    log.save()
    return log


def sync_deals(account, client: HubSpotClient) -> HubspotSyncLog:
    log = HubspotSyncLog.objects.create(
        account=account,
        entity_type=HubspotSyncLog.EntityType.DEAL,
        status=HubspotSyncLog.SyncStatus.RUNNING,
        sync_started_at=timezone.now(),
    )
    created = updated = 0
    try:
        for deal_data in client.get_all_deals():
            props = deal_data.get("properties", {})
            hubspot_deal_id = str(deal_data["id"])

            owner = None
            owner_id = props.get("hubspot_owner_id")
            if owner_id:
                owner = HubspotOwner.objects.filter(
                    hubspot_owner_id=owner_id, account=account
                ).first()

            customer = _find_customer_for_deal(account, deal_data, client)

            closed_won_at = None
            if props.get("dealstage") == "closedwon":
                closed_date = props.get("closedate")
                if closed_date:
                    closed_won_at = parse_hubspot_date(closed_date)

            defaults = {
                "account": account,
                "customer": customer,
                "owner": owner,
                "deal_name": props.get("dealname", "Unnamed Deal"),
                "amount": float(props.get("amount") or 0),
                "currency": "USD",
                "stage": props.get("dealstage", ""),
                "closed_won_at": closed_won_at,
                "expected_close_date": None,
                "raw_properties": props,
                "synced_at": timezone.now(),
                "is_deleted": False,
            }
            obj, was_created = Deal.objects.update_or_create(
                hubspot_deal_id=hubspot_deal_id,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        log.records_created = created
        log.records_updated = updated
        log.status = HubspotSyncLog.SyncStatus.SUCCESS
    except Exception as e:
        logger.exception("Deal sync failed: %s", e)
        log.status = HubspotSyncLog.SyncStatus.FAILED
        log.error_message = str(e)
    log.sync_ended_at = timezone.now()
    log.save()
    return log


def _find_customer_for_deal(account, deal_data, client):
    try:
        assoc_data = client.get_deal_associations(deal_data["id"])
        for a in assoc_data:
            obj_type = a.get("toObjectType") or a.get("type") or ""
            contact_id = a.get("toObjectId") or a.get("id") or ""
            if "contact" in obj_type.lower() and contact_id:
                customer = Customer.objects.filter(
                    hubspot_contact_id=contact_id, account=account
                ).first()
                if customer:
                    return customer
    except Exception:
        pass
    return None
