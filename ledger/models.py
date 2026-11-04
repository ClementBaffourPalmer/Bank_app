from django.db import models


class SampleTransaction(models.Model):
    class Type(models.TextChoices):
        CREDIT = "CREDIT", "Sample credit"
        DEBIT = "DEBIT", "Sample debit"

    class Status(models.TextChoices):
        POSTED = "POSTED", "Sample posted"
        PENDING = "PENDING", "Sample pending"

    account = models.ForeignKey(
        "accounts.DemoAccount",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    reference = models.CharField(max_length=24, unique=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_type = models.CharField(max_length=8, choices=Type.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.POSTED)
    occurred_at = models.DateTimeField(db_index=True)
    is_sample = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=["account", "-occurred_at"], name="ledger_acct_occurred_idx"),
            models.Index(fields=["account", "transaction_type"], name="ledger_acct_type_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="ledger_sampletx_amount_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(is_sample=True),
                name="ledger_sampletx_must_be_sample",
            ),
            models.UniqueConstraint(fields=["reference"], name="ledger_sampletx_reference_unique"),
        ]

    def __str__(self):
        return f"{self.reference} (sample)"
