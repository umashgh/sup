"""
pytest configuration for sup backend.

Shared fixtures for both unit (Django TestCase) and e2e (Playwright) tests.
"""

import django
import os

# Tell pytest-django which settings to use
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sup_backend.settings")


def pytest_configure(config):
    django.setup()
