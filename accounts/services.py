from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction

from accounts.models import DemoAccount, User, UserPreference, UserProfile, generate_account_number
from ledger.services import seed_sample_transactions

INITIAL_SIMULATED_BALANCE = Decimal(settings.INITIAL_SIMULATED_BALANCE)


class RegistrationError(Exception):
    pass


class DuplicateAccountError(RegistrationError):
    pass


def _unique_account_number():
    for _ in range(25):
        candidate = generate_account_number()
        if not DemoAccount.objects.filter(account_number=candidate).exists():
            return candidate
    raise RegistrationError("Could not allocate a unique demonstration account number.")


@transaction.atomic
def register_user(
    *,
    first_name: str,
    last_name: str,
    email: str,
    username: str,
    password: str,
    phone: str = "",
    name=None,
):
    """Create a user, profile, preferences, and one fictional academic account."""
    normalized_email = User.objects.normalize_email(email)
    cleaned_username = username.strip()
    cleaned_first = first_name.strip()
    cleaned_last = last_name.strip()
    full_name = (name or f"{cleaned_first} {cleaned_last}").strip()

    if User.objects.filter(email__iexact=normalized_email).exists():
        raise DuplicateAccountError("An account with this email already exists.")
    if User.objects.filter(username__iexact=cleaned_username).exists():
        raise DuplicateAccountError("This username is already taken.")

    try:
        user = User.objects.create_user(
            email=normalized_email,
            password=password,
            username=cleaned_username,
            first_name=cleaned_first,
            last_name=cleaned_last,
            name=full_name,
        )
    except IntegrityError as exc:
        raise DuplicateAccountError(
            "An account with this email or username already exists."
        ) from exc

    UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "preferred_name": cleaned_first or full_name,
            "phone": (phone or "").strip(),
        },
    )
    UserPreference.objects.get_or_create(user=user)

    account, created = DemoAccount.objects.get_or_create(
        user=user,
        defaults={
            "account_number": _unique_account_number(),
            "available_balance": INITIAL_SIMULATED_BALANCE,
            "currency": "USD",
        },
    )
    if created:
        seed_sample_transactions(account)
    return user


def ensure_demo_account(user: User) -> DemoAccount:
    """Idempotently attach one demo account. Never reset an existing balance."""
    account, created = DemoAccount.objects.get_or_create(
        user=user,
        defaults={
            "account_number": _unique_account_number(),
            "available_balance": INITIAL_SIMULATED_BALANCE,
            "currency": "USD",
        },
    )
    if created:
        seed_sample_transactions(account)
    UserProfile.objects.get_or_create(
        user=user,
        defaults={"preferred_name": user.get_short_name()},
    )
    UserPreference.objects.get_or_create(user=user)
    return account
