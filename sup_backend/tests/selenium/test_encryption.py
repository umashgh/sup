"""
Encryption feature tests.

Covers:
- Login page shows encryption setup section when user has no encryption
- User can set up encryption via the API endpoint
- After encryption, the DB has a UserEncryption record (no plaintext payload)
- User can decrypt (login) with the correct passphrase
- Wrong passphrase shows passphrase_error on login page
"""
import json
import uuid

import pytest
import requests as _requests
from django.contrib.auth.models import User
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

pytestmark = pytest.mark.django_db(transaction=True)

WAIT = 10
PASSPHRASE = "test-passphrase-123"


# ---------------------------------------------------------------------------
# Helper: requests session authenticated as a real user
# ---------------------------------------------------------------------------

class AuthSession:
    """Requests session authenticated as a specific real user."""

    def __init__(self, base_url: str, username: str):
        self.base_url = base_url.rstrip("/")
        self.session = _requests.Session()
        self.username = username
        self._login()

    def _csrf(self):
        return self.session.cookies.get("csrftoken", "")

    def _headers(self):
        return {
            "X-CSRFToken": self._csrf(),
            "Referer": self.base_url,
            "Content-Type": "application/json",
        }

    def _login(self):
        """Log in as the given username via POST /accounts/login/."""
        # Get CSRF cookie first
        self.session.get(f"{self.base_url}/accounts/login/")
        resp = self.session.post(
            f"{self.base_url}/accounts/login/",
            data={
                "username": self.username,
                "csrfmiddlewaretoken": self._csrf(),
                "next": "/",
            },
            headers={"Referer": self.base_url},
            allow_redirects=True,
        )
        resp.raise_for_status()

    def post_json(self, path: str, data: dict) -> dict:
        url = f"{self.base_url}{path}"
        resp = self.session.post(url, json=data, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def setup_encryption(self, passphrase: str, hint: str = "") -> dict:
        return self.post_json(
            "/accounts/setup-encryption/",
            {"passphrase": passphrase, "hint": hint},
        )

    def remove_encryption(self, passphrase: str) -> dict:
        return self.post_json(
            "/accounts/remove-encryption/",
            {"passphrase": passphrase},
        )


# ---------------------------------------------------------------------------
# Tests: login page encryption UI
# ---------------------------------------------------------------------------

class TestEncryptionLoginUI:
    def test_encryption_setup_section_visible_for_new_user(self, driver, live_server, db):
        """
        When a user has NO encryption set up, the login page must display the
        encryption setup section (id='encSetupSection') in a visible state.
        """
        username = f"enc_test_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        driver.get(f"{live_server.url}/accounts/login/")
        # Fill username to trigger the check-encryption AJAX call
        username_input = WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.send_keys(username)

        # Wait for JS to check encryption status and reveal setup section
        WebDriverWait(driver, WAIT).until(
            lambda d: d.find_element(By.ID, "encSetupSection").is_displayed()
            or d.find_element(By.ID, "encSetupSection").get_attribute("style") != "display: none;"
        )
        setup_section = driver.find_element(By.ID, "encSetupSection")
        # The section may have display:block (shown) or be toggled by JS to block
        assert "none" not in (setup_section.get_attribute("style") or "block"), (
            "encSetupSection should not be hidden for a user without encryption"
        )

    def test_passphrase_field_hidden_for_new_user(self, driver, live_server, db):
        """
        A user with no encryption must NOT see the passphrase field on page load.
        """
        username = f"enc_test_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        # Navigate to login with ?u= pre-fill so server sets has_encryption=False
        driver.get(f"{live_server.url}/accounts/login/?u={username}")

        passphrase_block = WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.ID, "passphraseBlock"))
        )
        style = passphrase_block.get_attribute("style") or ""
        assert "display: none" in style or "display:none" in style, (
            "Passphrase block should be hidden for a user with no encryption"
        )

    def test_passphrase_field_visible_for_encrypted_user(self, driver, live_server, db):
        """
        After setting up encryption, visiting /accounts/login/?u=<username>
        must show the passphrase input field immediately (server-side has_encryption=True).
        """
        username = f"enc_test_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        # Set up encryption via API
        auth = AuthSession(live_server.url, username)
        result = auth.setup_encryption(PASSPHRASE, hint="test hint")
        assert result.get("success"), f"Encryption setup failed: {result}"

        # Navigate to login with pre-fill
        driver.get(f"{live_server.url}/accounts/login/?u={username}")

        passphrase_block = WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.ID, "passphraseBlock"))
        )
        style = passphrase_block.get_attribute("style") or ""
        assert "display: none" not in style and "display:none" not in style, (
            "Passphrase block should be visible for a user with encryption"
        )

    def test_encryption_hint_shown_when_set(self, driver, live_server, db):
        """When an encryption hint is set, it appears on the login page."""
        username = f"enc_test_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        auth = AuthSession(live_server.url, username)
        auth.setup_encryption(PASSPHRASE, hint="my secret hint text")

        driver.get(f"{live_server.url}/accounts/login/?u={username}")
        WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.ID, "passphraseHintText"))
        )
        hint_el = driver.find_element(By.ID, "passphraseHintText")
        assert "my secret hint text" in hint_el.text, (
            f"Hint text not shown: {hint_el.text!r}"
        )


# ---------------------------------------------------------------------------
# Tests: encryption setup via API
# ---------------------------------------------------------------------------

class TestEncryptionSetupAPI:
    def test_setup_encryption_creates_db_record(self, live_server, db):
        """
        After calling /accounts/setup-encryption/, a UserEncryption record
        must exist in the database for that user.
        """
        from core.models import UserEncryption

        username = f"enc_api_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        auth = AuthSession(live_server.url, username)
        result = auth.setup_encryption(PASSPHRASE)
        assert result.get("success"), f"Expected success=True: {result}"

        user = User.objects.get(username=username)
        assert UserEncryption.objects.filter(user=user).exists(), (
            "UserEncryption record not created after setup"
        )

    def test_short_passphrase_rejected(self, live_server, db):
        """
        A passphrase shorter than 4 characters must be rejected by the API.
        """
        username = f"enc_api_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        auth = AuthSession(live_server.url, username)
        result = auth.setup_encryption("abc")  # 3 chars — too short
        assert not result.get("success"), (
            f"Short passphrase should be rejected, got: {result}"
        )
        assert "error" in result, "Error message expected for short passphrase"

    def test_encryption_record_has_kdf_salt(self, live_server, db):
        """
        The UserEncryption record must store a non-empty kdf_salt,
        proving KDF was applied (not plaintext storage).
        """
        from core.models import UserEncryption

        username = f"enc_api_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        auth = AuthSession(live_server.url, username)
        auth.setup_encryption(PASSPHRASE)

        user = User.objects.get(username=username)
        ue = UserEncryption.objects.get(user=user)
        assert ue.kdf_salt, "kdf_salt must be set (passphrase is KDF-derived, not stored)"
        assert ue.verification_token, "verification_token must be set"

    def test_encryption_data_not_plain_passphrase(self, live_server, db):
        """
        The passphrase must NOT be stored in plaintext in the UserEncryption model.
        kdf_salt and verification_token are binary/base64, not the passphrase itself.
        """
        from core.models import UserEncryption

        username = f"enc_api_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        auth = AuthSession(live_server.url, username)
        auth.setup_encryption(PASSPHRASE)

        user = User.objects.get(username=username)
        ue = UserEncryption.objects.get(user=user)

        # Passphrase must not appear verbatim in any stored field
        for field_name in ["kdf_salt", "verification_token", "passphrase_hint"]:
            val = str(getattr(ue, field_name, "") or "")
            assert PASSPHRASE not in val, (
                f"Passphrase stored in plaintext in UserEncryption.{field_name}!"
            )


# ---------------------------------------------------------------------------
# Tests: login with wrong / correct passphrase
# ---------------------------------------------------------------------------

class TestEncryptionLogin:
    def _setup_user_with_encryption(self, live_server, db_fixture_not_needed):
        """Create a user and set up encryption on them. Return username."""
        username = f"enc_login_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)
        auth = AuthSession(live_server.url, username)
        result = auth.setup_encryption(PASSPHRASE)
        assert result.get("success"), f"Setup failed: {result}"
        return username

    def test_correct_passphrase_logs_in(self, driver, live_server, db):
        """
        Entering the correct passphrase on the login form must log the user in
        and redirect away from /accounts/login/.
        """
        username = self._setup_user_with_encryption(live_server, None)

        driver.get(f"{live_server.url}/accounts/logout/")
        WebDriverWait(driver, WAIT).until(EC.url_contains(live_server.url))

        driver.get(f"{live_server.url}/accounts/login/?u={username}")
        username_input = WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.clear()
        username_input.send_keys(username)

        # Wait for passphrase field to appear
        WebDriverWait(driver, WAIT).until(
            EC.visibility_of_element_located((By.ID, "passphraseInput"))
        )
        driver.find_element(By.ID, "passphraseInput").send_keys(PASSPHRASE)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(driver, WAIT).until(
            lambda d: "/accounts/login/" not in d.current_url
        )

    def test_wrong_passphrase_shows_error(self, driver, live_server, db):
        """
        Entering the wrong passphrase must keep the user on the login page
        and show a passphrase error message.
        """
        username = self._setup_user_with_encryption(live_server, None)

        driver.get(f"{live_server.url}/accounts/logout/")
        WebDriverWait(driver, WAIT).until(EC.url_contains(live_server.url))

        driver.get(f"{live_server.url}/accounts/login/?u={username}")
        username_input = WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.clear()
        username_input.send_keys(username)

        WebDriverWait(driver, WAIT).until(
            EC.visibility_of_element_located((By.ID, "passphraseInput"))
        )
        driver.find_element(By.ID, "passphraseInput").send_keys("WRONG-PASSPHRASE")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Must stay on login page
        WebDriverWait(driver, WAIT).until(EC.url_contains("/accounts/login/"))

        # Must show an error message
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert any(kw in body_text for kw in ["incorrect", "wrong", "passphrase"]), (
            f"Expected passphrase error on page, body was: {body_text[:300]!r}"
        )

    def test_remove_encryption_api(self, live_server, db):
        """
        POST /accounts/remove-encryption/ with correct passphrase should
        remove the UserEncryption record from the database.
        """
        from core.models import UserEncryption

        username = self._setup_user_with_encryption(live_server, None)
        user = User.objects.get(username=username)
        assert UserEncryption.objects.filter(user=user).exists(), "Pre-condition: encryption exists"

        auth = AuthSession(live_server.url, username)
        result = auth.remove_encryption(PASSPHRASE)
        assert result.get("success"), f"Remove encryption failed: {result}"

        user.refresh_from_db()
        assert not UserEncryption.objects.filter(user=user).exists(), (
            "UserEncryption record should be deleted after removal"
        )

    def test_wrong_passphrase_on_remove_fails(self, live_server, db):
        """
        POST /accounts/remove-encryption/ with wrong passphrase must return
        success=False and leave the encryption record intact.
        """
        from core.models import UserEncryption

        username = self._setup_user_with_encryption(live_server, None)

        auth = AuthSession(live_server.url, username)
        result = auth.remove_encryption("totally-wrong-passphrase")
        assert not result.get("success"), f"Expected failure, got: {result}"

        user = User.objects.get(username=username)
        assert UserEncryption.objects.filter(user=user).exists(), (
            "Encryption should still exist after failed removal attempt"
        )


# ---------------------------------------------------------------------------
# Tests: check-encryption endpoint
# ---------------------------------------------------------------------------

class TestCheckEncryptionEndpoint:
    def test_check_encryption_false_for_new_user(self, live_server, db):
        """GET /accounts/check-encryption/?u=<username> → has_encryption=False for new users."""
        username = f"enc_chk_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        s = _requests.Session()
        resp = s.get(f"{live_server.url}/accounts/check-encryption/?u={username}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_encryption"] is False

    def test_check_encryption_true_after_setup(self, live_server, db):
        """GET /accounts/check-encryption/?u=<username> → has_encryption=True after setup."""
        username = f"enc_chk_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        auth = AuthSession(live_server.url, username)
        auth.setup_encryption(PASSPHRASE, hint="my hint")

        s = _requests.Session()
        resp = s.get(f"{live_server.url}/accounts/check-encryption/?u={username}")
        data = resp.json()
        assert data["has_encryption"] is True

    def test_check_encryption_returns_hint(self, live_server, db):
        """The hint is returned alongside has_encryption=True."""
        username = f"enc_chk_{uuid.uuid4().hex[:6]}"
        User.objects.create_user(username=username)

        auth = AuthSession(live_server.url, username)
        auth.setup_encryption(PASSPHRASE, hint="remember summer 2023")

        s = _requests.Session()
        resp = s.get(f"{live_server.url}/accounts/check-encryption/?u={username}")
        data = resp.json()
        assert data["hint"] == "remember summer 2023"
