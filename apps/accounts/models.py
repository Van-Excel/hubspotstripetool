from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.accounts.managers import CustomUserManager
from apps.core.models import CommonField


class User(CommonField, AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.email


class Role(CommonField):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField("Permission", related_name="roles")

    def __str__(self):
        return self.name


class Permission(CommonField):
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.codename


class Account(CommonField):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="account",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="accounts",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.full_name or self.user.email
