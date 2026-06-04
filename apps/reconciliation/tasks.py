import logging
from celery import shared_task
from apps.accounts.models import Account
from apps.reconciliation.engine import ReconciliationEngine

logger = logging.getLogger(__name__)


@shared_task(name="run_reconciliation")
def run_reconciliation():
    account = Account.objects.select_related("user").first()
    if not account:
        return {"error": "No account found"}
    engine = ReconciliationEngine()
    run = engine.run(account)
    return {
        "status": run.status,
        "anomalies_found": run.anomalies_found,
        "deals_processed": run.deals_processed,
        "id": str(run.identifier),
    }
