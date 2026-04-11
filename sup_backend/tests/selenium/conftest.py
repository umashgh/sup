"""
Shared pytest fixtures for Selenium tests.
"""
import uuid

import pytest
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

MOBILE_WIDTH = 375
MOBILE_HEIGHT = 812


def _build_chrome_options() -> Options:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument(f"--window-size={MOBILE_WIDTH},{MOBILE_HEIGHT}")
    # Emulate a mobile user-agent so the server sees a real mobile client
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    )
    return opts


@pytest.fixture(scope="function")
def driver():
    """Headless Chrome driver with 375×812 mobile viewport."""
    service = Service(ChromeDriverManager().install())
    opts = _build_chrome_options()
    drv = webdriver.Chrome(service=service, options=opts)
    drv.set_window_size(MOBILE_WIDTH, MOBILE_HEIGHT)
    yield drv
    drv.quit()


@pytest.fixture(scope="function")
def guest_session(driver, live_server):
    """
    Navigate to '/' and start a guest session via POST /start/.
    Returns the driver already on the scenario selector page.
    """
    driver.get(f"{live_server.url}/start/")
    # /start/ redirects to '/' (scenario_selector) for non-AJAX requests
    return driver


@pytest.fixture(scope="function")
def logged_in_user(driver, live_server, db):
    """
    Create a real Django test user and log them in via the login form.
    Returns (driver, user) with the browser already on the scenario selector.
    """
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    user = User.objects.create_user(username=username)

    driver.get(f"{live_server.url}/accounts/login/")

    username_input = driver.find_element("name", "username")
    username_input.clear()
    username_input.send_keys(username)

    driver.find_element("css selector", "button[type='submit']").click()

    return driver, user
