from celery import shared_task
from apps.crm.services.hubspot_client import HubSpotClient
from apps.crm.services.sync import sync_owners, sync_contacts, sync_deals
from apps.accounts.models import Account


def _get_first_account():
    return Account.objects.select_related("user").first()


@shared_task(name="sync_hubspot_all")
def sync_hubspot_all():
    account = _get_first_account()
    if not account:
        return {"error": "No account found"}
    client = HubSpotClient()
    sync_owners(account, client)
    sync_contacts(account, client)
    sync_deals(account, client)
    return {"status": "completed"}


@shared_task(name="run_reconciliation_after_sync")
def run_reconciliation_after_sync():
    from apps.reconciliation.tasks import run_reconciliation
    run_reconciliation.delay()
