import uuid
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from ledger.models import SampleTransaction

SAMPLE_ACTIVITY = (
    ("Payroll sample — software demo", "CREDIT", "28450.00", "POSTED", 2),
    ("Vendor settlement sample", "DEBIT", "6120.40", "POSTED", 5),
    ("Treasury sweep sample", "CREDIT", "150000.00", "POSTED", 8),
    ("Card settlement sample", "DEBIT", "842.19", "POSTED", 9),
    ("Interest accrual sample", "CREDIT", "210.55", "POSTED", 12),
    ("Operating expense sample", "DEBIT", "4300.00", "POSTED", 14),
    ("Client retainer sample", "CREDIT", "25000.00", "PENDING", 16),
    ("Cloud infrastructure sample", "DEBIT", "1188.00", "POSTED", 18),
    ("Tax remittance sample", "DEBIT", "9900.00", "POSTED", 21),
    ("Fee rebate sample", "CREDIT", "75.00", "POSTED", 24),
    ("Office lease sample", "DEBIT", "7200.00", "POSTED", 27),
    ("Reserve allocation sample", "DEBIT", "50000.00", "POSTED", 30),
)


def _reference():
    return "SMP-" + uuid.uuid4().hex[:12].upper()


def seed_sample_transactions(account):
    """Attach generated sample rows. These do not represent real payments."""
    now = timezone.now()
    rows = []
    for description, tx_type, amount, status, days_ago in SAMPLE_ACTIVITY:
        rows.append(
            SampleTransaction(
                account=account,
                reference=_reference(),
                description=f"SAMPLE · {description}",
                amount=Decimal(amount),
                transaction_type=tx_type,
                status=status,
                occurred_at=now - timedelta(days=days_ago),
                is_sample=True,
            )
        )
    SampleTransaction.objects.bulk_create(rows)
    return rows
