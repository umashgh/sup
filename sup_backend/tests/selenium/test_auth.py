"""
Authentication and session tests.

Covers:
- Guest session created on landing (no login required)
- Registered user can log in via /accounts/login/
- Session persists across page reload
- Logout clears the session
"""
import uuid

import pytest
from django.contrib.auth.models import User
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

pytestmark = pytest.mark.django_db(transaction=True)

WAIT = 10  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_for_url_contains(driver, fragment: str, timeout: int = WAIT):
    WebDriverWait(driver, timeout).until(EC.url_contains(fragment))


def _wait_for_element(driver, by, value, timeout: int = WAIT):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGuestSession:
    def test_landing_page_loads_without_login(self, driver, live_server):
        """
        The root URL '/' must be reachable without any login.
        It should render the scenario selector page.
        """
        driver.get(live_server.url + "/")
        assert driver.title, "Page has no title — may have failed to load"
        # Scenario selector renders story cards
        _wait_for_element(driver, By.CSS_SELECTOR, ".story")

    def test_guest_session_created_via_start(self, driver, live_server):
        """
        POST /start/ creates a guest user and redirects to the scenario selector.
        The user is now authenticated (guest_<uuid> username).
        """
        driver.get(live_server.url + "/start/")
        # After /start/ the server redirects to '/' (scenario_selector)
        _wait_for_url_contains(driver, live_server.url)
        # Scenario cards should be visible
        _wait_for_element(driver, By.CSS_SELECTOR, ".story[role='button']")

    def test_guest_session_does_not_require_signup(self, driver, live_server):
        """
        Visiting /start/ must NOT redirect to the login page — guest access
        is always available.
        """
        driver.get(live_server.url + "/start/")
        WebDriverWait(driver, WAIT).until(lambda d: d.current_url != live_server.url + "/start/")
        assert "/accounts/login/" not in driver.current_url, (
            "Guest start redirected to login page — guest access should not require authentication"
        )

    def test_multiple_start_calls_reuse_session(self, driver, live_server):
        """
        If the user is already authenticated (e.g. already hit /start/),
        a second visit to /start/ should redirect to '/' without creating a new guest.
        """
        driver.get(live_server.url + "/start/")
        _wait_for_element(driver, By.CSS_SELECTOR, ".story")
        first_url = driver.current_url

        driver.get(live_server.url + "/start/")
        _wait_for_element(driver, By.CSS_SELECTOR, ".story")
        second_url = driver.current_url

        assert first_url == second_url, (
            "Second /start/ visit landed on a different page — session may not be reused"
        )


class TestRegisteredUserLogin:
    def test_login_page_renders(self, driver, live_server):
        """GET /accounts/login/ renders a form with a username input."""
        driver.get(live_server.url + "/accounts/login/")
        username_input = _wait_for_element(driver, By.NAME, "username")
        assert username_input.is_displayed()

    def test_registered_user_can_log_in(self, driver, live_server, db):
        """
        A user created in the DB can sign in via the login form.
        After POST the browser redirects to the scenario selector.
        """
        username = f"testuser_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        driver.get(live_server.url + "/accounts/login/")
        username_input = _wait_for_element(driver, By.NAME, "username")
        username_input.send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Should land on scenario selector (root or /questions/ depending on progress)
        WebDriverWait(driver, WAIT).until(
            lambda d: "/accounts/login/" not in d.current_url
        )
        # Confirm we're on a page that has scenario or questions content
        assert any(
            path in driver.current_url
            for path in ["/", "/questions/", "/results/"]
        ), f"Unexpected redirect after login: {driver.current_url}"

    def test_unknown_username_shows_not_found(self, driver, live_server, db):
        """
        Submitting a username that does not exist should keep the user on
        the login page and display a 'not found' message.
        """
        driver.get(live_server.url + "/accounts/login/")
        username_input = _wait_for_element(driver, By.NAME, "username")
        username_input.send_keys("definitely_not_a_real_user_xyz987")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Stay on login page
        WebDriverWait(driver, WAIT).until(EC.url_contains("/accounts/login/"))

        # Some 'not found' indication in the page body
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert any(kw in body_text for kw in ["no account", "not found", "sign up", "create"]), (
            "Login with unknown username did not show a 'not found' message"
        )


class TestSessionPersistence:
    def test_session_persists_across_reload(self, driver, live_server, db):
        """
        After logging in, reloading the page should keep the user authenticated
        (not redirect to login).
        """
        username = f"testuser_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        # Log in
        driver.get(live_server.url + "/accounts/login/")
        _wait_for_element(driver, By.NAME, "username").send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(driver, WAIT).until(
            lambda d: "/accounts/login/" not in d.current_url
        )
        url_after_login = driver.current_url

        # Reload
        driver.refresh()
        WebDriverWait(driver, WAIT).until(EC.url_contains(url_after_login.split(live_server.url)[1]))

        assert "/accounts/login/" not in driver.current_url, (
            "Session was lost after page reload — user was redirected to login"
        )

    def test_guest_session_persists_across_reload(self, driver, live_server):
        """
        A guest session created via /start/ should survive a page reload.
        """
        driver.get(live_server.url + "/start/")
        _wait_for_element(driver, By.CSS_SELECTOR, ".story")
        url_before = driver.current_url

        driver.refresh()
        _wait_for_element(driver, By.CSS_SELECTOR, ".story")

        assert "/accounts/login/" not in driver.current_url, (
            "Guest session lost after reload — user redirected to login"
        )


class TestLogout:
    def test_logout_redirects_to_landing(self, driver, live_server, db):
        """
        After logging in, visiting /accounts/logout/ clears the session
        and redirects to the landing page ('/').
        """
        username = f"testuser_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        # Log in
        driver.get(live_server.url + "/accounts/login/")
        _wait_for_element(driver, By.NAME, "username").send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(driver, WAIT).until(
            lambda d: "/accounts/login/" not in d.current_url
        )

        # Log out
        driver.get(live_server.url + "/accounts/logout/")
        WebDriverWait(driver, WAIT).until(EC.url_contains(live_server.url))

        # Should be on root '/' after logout (signout redirects to '/')
        assert driver.current_url.rstrip("/") == live_server.url.rstrip("/"), (
            f"Logout landed on {driver.current_url!r} instead of root"
        )

    def test_after_logout_protected_content_not_accessible(self, driver, live_server, db):
        """
        After logout, visiting /ops/ (login-required view) should redirect
        to the login page.
        """
        username = f"testuser_{uuid.uuid4().hex[:6]}"
        User.objects.create_superuser(username=username, password="", email="testuser@example.com")  # staff user

        # Log in
        driver.get(live_server.url + "/accounts/login/")
        _wait_for_element(driver, By.NAME, "username").send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(driver, WAIT).until(
            lambda d: "/accounts/login/" not in d.current_url
        )

        # Log out
        driver.get(live_server.url + "/accounts/logout/")
        WebDriverWait(driver, WAIT).until(EC.url_contains(live_server.url))

        # Attempt to access a login-required page
        driver.get(live_server.url + "/ops/")
        WebDriverWait(driver, WAIT).until(lambda d: d.current_url != live_server.url + "/ops/")
        assert "/accounts/login/" in driver.current_url, (
            f"After logout, /ops/ was accessible without re-authentication: {driver.current_url}"
        )

    def test_sign_out_link_visible_when_logged_in(self, driver, live_server, db):
        """
        A 'Sign out' link should appear on the scenario selector when
        a real (non-guest) user is logged in.
        """
        username = f"testuser_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        driver.get(live_server.url + "/accounts/login/")
        _wait_for_element(driver, By.NAME, "username").send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(driver, WAIT).until(
            lambda d: "/accounts/login/" not in d.current_url
        )

        # Navigate to landing
        driver.get(live_server.url + "/")
        _wait_for_element(driver, By.CSS_SELECTOR, ".story")

        logout_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='logout']")
        assert logout_links, "No logout link visible for authenticated user on landing page"
