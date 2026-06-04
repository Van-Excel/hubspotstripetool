from apps.audit.models import AuditLog


def log_action(user, action, entity_type, entity_id, old_values=None, new_values=None, ip_address=None):
    if user is None or not user.is_authenticated:
        return None
    try:
        account = user.account
    except Exception:
        account = None
    return AuditLog.objects.create(
        account=account,
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
    )
