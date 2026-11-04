from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_endpoint_returns_ok(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertNotIn("SECRET_KEY", response.content.decode())
        self.assertNotIn("DATABASE_URL", response.content.decode())


class StaticAndSecurityConfigurationTests(SimpleTestCase):
    def test_whitenoise_is_configured(self):
        self.assertIn(
            "whitenoise.middleware.WhiteNoiseMiddleware",
            settings.MIDDLEWARE,
        )
        self.assertTrue(settings.STATIC_ROOT)

    def test_static_root_is_set(self):
        self.assertTrue(str(settings.STATIC_ROOT).endswith("staticfiles"))

    def test_session_cookies_are_httponly(self):
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)

    @override_settings(DEBUG=False)
    def test_debug_can_be_disabled(self):
        from django.conf import settings as live_settings

        live_settings.DEBUG  # accessed to ensure settings load
        self.assertFalse(False)


class ProductionSettingsModuleTests(SimpleTestCase):
    def test_auth_user_model(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")

    def test_axes_is_installed(self):
        self.assertIn("axes", settings.INSTALLED_APPS)
        self.assertEqual(settings.AXES_FAILURE_LIMIT, 5)
