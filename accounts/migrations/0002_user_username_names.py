# Generated manually for Citi Bank Academic Banking Application

from decimal import Decimal

import django.core.validators
from django.db import migrations, models


def backfill_usernames_and_names(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    used = set()
    for user in User.objects.all().order_by("id"):
        base = (user.email or f"user{user.pk}").split("@")[0].lower()
        base = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in base) or f"user{user.pk}"
        candidate = base
        suffix = 1
        while candidate.lower() in used or User.objects.filter(username__iexact=candidate).exclude(pk=user.pk).exists():
            candidate = f"{base}{suffix}"
            suffix += 1
        used.add(candidate.lower())
        user.username = candidate

        parts = (user.name or "").strip().split(None, 1)
        if not user.first_name:
            user.first_name = parts[0] if parts else "Member"
        if not user.last_name:
            user.last_name = parts[1] if len(parts) > 1 else "Account"
        user.save(update_fields=["username", "first_name", "last_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="first_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="user",
            name="last_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="user",
            name="username",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.RunPython(backfill_usernames_and_names, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(max_length=150, unique=True),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(fields=("username",), name="accounts_user_username_unique"),
        ),
        migrations.AlterField(
            model_name="demoaccount",
            name="available_balance",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Fictional academic project balance. Not real funds.",
                max_digits=14,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
            ),
        ),
    ]
