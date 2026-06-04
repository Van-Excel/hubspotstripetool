from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    codename = None

    def __init__(self, codename=None):
        if codename is not None:
            self.codename = codename

    def __call__(self):
        return self

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            account = request.user.account
        except Exception:
            return False
        if not account or not account.role:
            return False
        return account.role.permissions.filter(codename=self.codename).exists()


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.account.role.name == "admin"
        except Exception:
            return False
