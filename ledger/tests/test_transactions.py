from django.test import TestCase
from django.urls import reverse

from accounts.services import register_user
from ledger.models import SampleTransaction

PASSWORD = "CorrectHorse9!"


class TransactionViewTests(TestCase):
    def setUp(self):
        self.user = register_user(
            first_name="Jordan",
            last_name="Hale",
            email="jordan@example.com",
            username="jordanhale",
            phone="555-0100",
            password=PASSWORD,
        )
        self.other = register_user(
            first_name="Other",
            last_name="User",
            email="other@example.com",
            username="otheruser",
            phone="555-0200",
            password=PASSWORD,
        )

    def test_transaction_search_and_filter(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("ledger:transactions"), {"q": "Payroll", "type": "CREDIT"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SAMPLE ·")
        self.assertContains(response, "Payroll")
        empty = self.client.get(reverse("ledger:transactions"), {"q": "no-such-reference"})
        self.assertContains(empty, "No matching records")

    def test_cannot_see_another_users_transactions(self):
        self.client.force_login(self.user)
        foreign = SampleTransaction.objects.filter(account=self.other.demo_account).first()
        page = self.client.get(reverse("ledger:transactions"))
        self.assertNotContains(page, foreign.reference)

    def test_unauthenticated_access_redirects(self):
        response = self.client.get(reverse("ledger:transactions"))
        self.assertEqual(response.status_code, 302)
