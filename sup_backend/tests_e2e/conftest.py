"""
E2E test fixtures.

Uses pytest-django's `live_server` to spin up a real Django server on a
random port, then drives it with Playwright's headless Chromium.

Mobile viewport (375×667 — iPhone SE) is used for all tests, matching
the app's design target.
"""

import pytest
from playwright.sync_api import Page, BrowserContext


MOBILE_VIEWPORT = {"width": 375, "height": 667}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Override default context args: mobile viewport + no animations."""
    return {
        **browser_context_args,
        "viewport": MOBILE_VIEWPORT,
        "is_mobile": True,
        "has_touch": True,
    }


@pytest.fixture
def app_url(live_server):
    """Return the live server root URL, e.g. http://127.0.0.1:PORT."""
    return live_server.url
