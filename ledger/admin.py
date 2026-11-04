from django.contrib import admin

from ledger.models import SampleTransaction


@admin.register(SampleTransaction)
class SampleTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "account",
        "transaction_type",
        "status",
        "amount",
        "occurred_at",
        "is_sample",
    )
    list_filter = ("transaction_type", "status", "is_sample")
    search_fields = ("reference", "description", "account__account_number")
    readonly_fields = ("created_at",)
