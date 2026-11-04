from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from accounts.services import ensure_demo_account
from ledger.models import SampleTransaction


@login_required
def transaction_list(request):
    account = ensure_demo_account(request.user)
    queryset = SampleTransaction.objects.filter(account=account).select_related("account")

    query = request.GET.get("q", "").strip()
    tx_type = request.GET.get("type", "").strip().upper()
    status = request.GET.get("status", "").strip().upper()

    if query:
        queryset = queryset.filter(
            Q(description__icontains=query) | Q(reference__icontains=query)
        )
    if tx_type in SampleTransaction.Type.values:
        queryset = queryset.filter(transaction_type=tx_type)
    if status in SampleTransaction.Status.values:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset, 10)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "app/transactions.html",
        {
            "account": account,
            "page": page,
            "query": query,
            "selected_type": tx_type,
            "selected_status": status,
            "is_empty": not queryset.exists(),
        },
    )
