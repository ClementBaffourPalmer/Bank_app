from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.AppLogoutView.as_view(), name="logout"),
    path("password-reset/", views.password_reset_view, name="password_reset"),
    path(
        "password-reset/sent/",
        views.AppPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        views.AppPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        views.AppPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("account/", views.account_details, name="account"),
    path("statements/", views.statements, name="statements"),
    path("profile/", views.profile_settings, name="profile"),
    path("dashboard/balance-visibility/", views.toggle_balance_visibility, name="toggle_balance"),
]
