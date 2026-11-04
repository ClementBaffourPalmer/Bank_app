from calendar import month_name
from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from accounts.forms import (
    EmailAuthenticationForm,
    ProfileForm,
    QuietPasswordResetForm,
    RegistrationForm,
    StyledSetPasswordForm,
)
from accounts.services import ensure_demo_account
from accounts.throttling import rate_limit
from ledger.models import SampleTransaction


def health_check(request):
    return JsonResponse({"status": "ok", "service": "prestige-wealth-bank"})


def landing(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return render(request, "marketing/landing.html")


@rate_limit("register", limit=8, window=300)
def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request,
            "Account created successfully. Sign in with your email or username to continue.",
        )
        return redirect("accounts:login")
    return render(request, "registration/register.html", {"form": form})


class ThrottledLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember = form.cleaned_data.get("remember_me")
        response = super().form_valid(form)
        if remember:
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            self.request.session.set_expiry(0)
        return response


login_view = rate_limit("login", limit=20, window=300)(ThrottledLoginView.as_view())


class AppLogoutView(LogoutView):
    http_method_names = ["get", "post", "head", "options"]


class ThrottledPasswordResetView(PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.txt"
    subject_template_name = "registration/password_reset_subject.txt"
    form_class = QuietPasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")


password_reset_view = rate_limit("password_reset", limit=5, window=600)(
    ThrottledPasswordResetView.as_view()
)


class AppPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class AppPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    form_class = StyledSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class AppPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"


@login_required
def dashboard(request):
    account = ensure_demo_account(request.user)
    recent = (
        SampleTransaction.objects.filter(account=account)
        .order_by("-occurred_at")[:6]
    )
    return render(
        request,
        "app/dashboard.html",
        {
            "account": account,
            "recent_transactions": recent,
        },
    )


@login_required
def account_details(request):
    demo = ensure_demo_account(request.user)
    return render(request, "app/account_details.html", {"account": demo})


@login_required
def statements(request):
    account = ensure_demo_account(request.user)
    transactions = SampleTransaction.objects.filter(account=account).order_by("-occurred_at")
    grouped = defaultdict(lambda: {"credits": Decimal("0.00"), "debits": Decimal("0.00"), "count": 0})
    for item in transactions:
        key = (item.occurred_at.year, item.occurred_at.month)
        bucket = grouped[key]
        bucket["count"] += 1
        if item.transaction_type == SampleTransaction.Type.CREDIT:
            bucket["credits"] += item.amount
        else:
            bucket["debits"] += item.amount
    statement_rows = [
        {
            "label": f"{month_name[month]} {year}",
            "year": year,
            "month": month,
            "credits": data["credits"],
            "debits": data["debits"],
            "count": data["count"],
            "net": data["credits"] - data["debits"],
        }
        for (year, month), data in sorted(grouped.items(), reverse=True)
    ]
    return render(
        request,
        "app/statements.html",
        {
            "account": account,
            "statement_rows": statement_rows,
        },
    )


@login_required
def profile_settings(request):
    ensure_demo_account(request.user)
    initial = {
        "first_name": request.user.first_name or request.user.get_short_name(),
        "last_name": request.user.last_name,
        "preferred_name": request.user.profile.preferred_name,
        "phone": request.user.profile.phone,
        "dark_mode": request.user.preferences.dark_mode,
    }
    form = ProfileForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        form.save(request.user)
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "app/profile.html", {"form": form})


@login_required
@require_POST
def toggle_balance_visibility(request):
    ensure_demo_account(request.user)
    preferences = request.user.preferences
    preferences.hide_balance = not preferences.hide_balance
    preferences.save(update_fields=["hide_balance", "updated_at"])
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"hide_balance": preferences.hide_balance})
    return redirect(request.POST.get("next") or "accounts:dashboard")
