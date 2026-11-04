import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


class ProductionEnvironmentTests(SimpleTestCase):
    def _import_settings(self, extra_env):
        env = os.environ.copy()
        env.pop("AURETA_TESTING", None)
        env.update(
            {
                "DJANGO_SETTINGS_MODULE": "config.settings",
                "DEBUG": "False",
                "PYTHONPATH": str(ROOT),
                **extra_env,
            }
        )
        return subprocess.run(
            [sys.executable, "-c", "import config.settings"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_missing_secret_key_fails_closed(self):
        result = self._import_settings(
            {
                "SECRET_KEY": "",
                "ALLOWED_HOSTS": "example.onrender.com",
                "CSRF_TRUSTED_ORIGINS": "https://example.onrender.com",
                "DATABASE_URL": "postgres://user:pass@localhost:5432/db",
            }
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY", result.stderr)

    def test_valid_production_env_imports(self):
        result = self._import_settings(
            {
                "SECRET_KEY": "production-secret-key-with-enough-entropy-123456",
                "ALLOWED_HOSTS": "example.onrender.com",
                "CSRF_TRUSTED_ORIGINS": "https://example.onrender.com",
                "DATABASE_URL": "postgres://user:pass@localhost:5432/db",
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
