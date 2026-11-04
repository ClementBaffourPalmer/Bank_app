from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import DemoAccount
from accounts.services import DuplicateAccountError, register_user

User = get_user_model()

INITIAL = Decimal("56075294.00")
PASSWORD = "CorrectHorse9!"


def make_user(**overrides):
    payload = {
        "first_name": "Jordan",
        "last_name": "Hale",
        "email": "jordan@example.com",
        "username": "jordanhale",
        "phone": "555-0100",
        "password": PASSWORD,
    }
    payload.update(overrides)
    return register_user(**payload)


class RegistrationTests(TestCase):
    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Jordan",
                "last_name": "Hale",
                "email": "jordan@example.com",
                "username": "jordanhale",
                "phone": "555-0100",
                "password": PASSWORD,
                "password_confirm": PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:login"))
        user = User.objects.get(email="jordan@example.com")
        self.assertEqual(user.username, "jordanhale")
        self.assertEqual(user.first_name, "Jordan")
        self.assertEqual(user.demo_account.available_balance, INITIAL)

    def test_duplicate_email_is_rejected(self):
        make_user()
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Other",
                "last_name": "Person",
                "email": "jordan@example.com",
                "username": "otherperson",
                "phone": "555-0199",
                "password": PASSWORD,
                "password_confirm": PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="jordan@example.com").count(), 1)
        with self.assertRaises(DuplicateAccountError):
            make_user(username="copyuser")

    def test_duplicate_username_is_rejected(self):
        make_user()
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Other",
                "last_name": "Person",
                "email": "other@example.com",
                "username": "jordanhale",
                "phone": "555-0199",
                "password": PASSWORD,
                "password_confirm": PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="other@example.com").exists())

    def test_login_with_email_and_username(self):
        make_user()
        email_login = self.client.post(
            reverse("accounts:login"),
            {"username": "jordan@example.com", "password": PASSWORD},
        )
        self.assertEqual(email_login.status_code, 302)
        self.assertTrue(self.client.session.get("_auth_user_id"))
        self.client.post(reverse("accounts:logout"))
        username_login = self.client.post(
            reverse("accounts:login"),
            {"username": "jordanhale", "password": PASSWORD},
        )
        self.assertEqual(username_login.status_code, 302)
        self.assertTrue(self.client.session.get("_auth_user_id"))

    def test_invalid_credentials_show_error(self):
        make_user()
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "jordan@example.com", "password": "WrongPassword1!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid email/username and password")

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_password_reset_does_not_reveal_registration(self):
        known = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "missing@example.com"},
        )
        self.assertEqual(known.status_code, 302)
        self.assertEqual(known.url, reverse("accounts:password_reset_done"))
        make_user()
        existing = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "jordan@example.com"},
        )
        self.assertEqual(existing.status_code, 302)
        self.assertEqual(existing.url, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

    def test_profile_update(self):
        make_user()
        self.client.force_login(User.objects.get(email="jordan@example.com"))
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Jordan",
                "last_name": "H.",
                "preferred_name": "Jo",
                "phone": "555-0100",
                "dark_mode": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="jordan@example.com")
        self.assertEqual(user.last_name, "H.")
        self.assertEqual(user.name, "Jordan H.")
        self.assertTrue(user.preferences.dark_mode)


class BalanceTests(TestCase):
    def test_initial_simulated_balance_created(self):
        user = make_user()
        account = DemoAccount.objects.get(user=user)
        self.assertEqual(account.available_balance, INITIAL)
        self.assertEqual(DemoAccount.objects.filter(user=user).count(), 1)
        self.client.force_login(user)
        dashboard = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(dashboard, "Welcome back, Jordan")
        self.assertContains(dashboard, "Available Balance")
        self.assertContains(dashboard, "56,075,294.00")

    def test_full_register_login_logout_journey(self):
        register = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Alex",
                "last_name": "Rivera",
                "email": "alex@example.com",
                "username": "alexrivera",
                "phone": "555-0111",
                "password": PASSWORD,
                "password_confirm": PASSWORD,
            },
        )
        self.assertEqual(register.status_code, 302)
        login = self.client.post(
            reverse("accounts:login"),
            {"username": "alexrivera", "password": PASSWORD},
        )
        self.assertEqual(login.status_code, 302)
        self.assertEqual(login.url, reverse("accounts:dashboard"))
        first = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(first, "Welcome back, Alex")
        self.assertContains(first, "56,075,294.00")
        self.client.post(reverse("accounts:logout"))
        again = self.client.post(
            reverse("accounts:login"),
            {"username": "alex@example.com", "password": PASSWORD},
        )
        self.assertEqual(again.status_code, 302)
        second = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(second, "56,075,294.00")
        account = DemoAccount.objects.get(user__email="alex@example.com")
        self.assertEqual(account.available_balance, INITIAL)

    def test_balance_persists_across_login(self):
        user = make_user()
        account = user.demo_account
        account.available_balance = Decimal("12345.67")
        account.save(update_fields=["available_balance"])
        self.client.force_login(user)
        self.client.get(reverse("accounts:dashboard"))
        self.client.logout()
        self.client.force_login(user)
        refreshed = DemoAccount.objects.get(user=user)
        self.assertEqual(refreshed.available_balance, Decimal("12345.67"))

    def test_accounts_are_isolated(self):
        first = make_user()
        second = make_user(
            first_name="Two",
            last_name="User",
            email="two@example.com",
            username="twouser",
            phone="555-0200",
        )
        self.assertNotEqual(first.demo_account.pk, second.demo_account.pk)
        self.client.force_login(first)
        page = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(page, first.demo_account.account_number)
        self.assertNotContains(page, second.demo_account.account_number)

    def test_user_uniqueness_constraint(self):
        user = make_user()
        with self.assertRaises(Exception):
            DemoAccount.objects.create(
                user=user,
                account_number="CBA-0000000001",
                available_balance=INITIAL,
            )

    def test_statements_requires_login_and_renders(self):
        user = make_user()
        blocked = self.client.get(reverse("accounts:statements"))
        self.assertEqual(blocked.status_code, 302)
        self.client.force_login(user)
        page = self.client.get(reverse("accounts:statements"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Account statements")
