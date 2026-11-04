import secrets
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


username_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9_.-]+$",
    message="Username may contain letters, numbers, dots, hyphens, and underscores only.",
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        first_name = (extra_fields.get("first_name") or "").strip()
        last_name = (extra_fields.get("last_name") or "").strip()
        name = (extra_fields.get("name") or "").strip()
        if not name:
            name = f"{first_name} {last_name}".strip()
        if not name:
            raise ValueError("A name is required.")
        extra_fields["name"] = name
        if first_name:
            extra_fields["first_name"] = first_name
        if last_name:
            extra_fields["last_name"] = last_name
        username = (extra_fields.get("username") or "").strip()
        if not username:
            raise ValueError("A username is required.")
        extra_fields["username"] = username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("username", email.split("@")[0])
        extra_fields.setdefault("first_name", "Admin")
        extra_fields.setdefault("last_name", "User")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email address", unique=True)
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    name = models.CharField(max_length=150)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["email"], name="accounts_user_email_unique"),
            models.UniqueConstraint(fields=["username"], name="accounts_user_username_unique"),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        composed = f"{self.first_name} {self.last_name}".strip()
        return composed or self.name

    def get_short_name(self):
        if self.first_name:
            return self.first_name
        return self.name.split()[0] if self.name else self.username


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=32, blank=True)
    preferred_name = models.CharField(max_length=150, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.email}"


class UserPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    dark_mode = models.BooleanField(default=False)
    hide_balance = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.email}"


def generate_account_number():
    return "CBA-" + "".join(secrets.choice("0123456789") for _ in range(10))


class DemoAccount(models.Model):
    """Personal fictional academic account with a stored demonstration balance."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="demo_account",
    )
    account_number = models.CharField(max_length=16, unique=True)
    currency = models.CharField(max_length=3, default="USD")
    available_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Fictional academic project balance. Not real funds.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user"], name="accounts_demoaccount_one_per_user"),
            models.CheckConstraint(
                condition=models.Q(available_balance__gte=0),
                name="accounts_demoaccount_balance_gte_zero",
            ),
        ]

    def __str__(self):
        return f"{self.account_number} ({self.user.email})"
