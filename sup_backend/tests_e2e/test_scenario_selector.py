"""
E2E tests — Scenario Selector page  (/)

Covers:
  - Page loads with correct title / branding
  - All 5 scenario cards are present and labelled
  - Clicking a scenario triggers guest login and redirects to /questions/
  - Error state is absent on clean load
"""

import pytest
from playwright.sync_api import Page, expect


pytestmark = pytest.mark.django_db(transaction=True)

SCENARIOS = ["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"]
SCENARIO_LABELS = {
    "FOUNDER":     "Startup Founder",
    "RETIREMENT":  "Retirement",
    "R2I":         "Return to India",
    "HALF_FIRE":   "Half-FIRE",
    "TERMINATION": "Layoff",
}


class TestScenarioSelectorPage:

    def test_page_loads(self, page: Page, app_url: str):
        page.goto(app_url + "/")
        expect(page).not_to_have_title("")
        # Brand name should be visible
        expect(page.locator("text=salaryfree").first).to_be_visible()

    def test_five_scenario_cards_present(self, page: Page, app_url: str):
        page.goto(app_url + "/")
        # Wait for Alpine.js to hydrate
        page.wait_for_load_state("networkidle")
        for scenario in SCENARIOS:
            locator = page.locator(f"[\\@click*=\"selectScenario('{scenario}')\"]")
            assert locator.count() > 0, f"Scenario card for {scenario} not found"

    def test_no_error_card_on_load(self, page: Page, app_url: str):
        page.goto(app_url + "/")
        page.wait_for_load_state("networkidle")
        error_cards = page.locator(".error-card")
        expect(error_cards).to_have_count(0)

    def test_selecting_founder_redirects_to_questions(self, page: Page, app_url: str):
        page.goto(app_url + "/")
        page.wait_for_load_state("networkidle")
        # Click FOUNDER scenario card
        page.locator("[\\@click*=\"selectScenario('FOUNDER')\"]").click()
        # Should land on /questions/ (guest login + scenario select happen via JS)
        page.wait_for_url("**/questions/", timeout=10_000)
        assert "/questions/" in page.url

    def test_selecting_retirement_redirects_to_questions(self, page: Page, app_url: str):
        page.goto(app_url + "/")
        page.wait_for_load_state("networkidle")
        page.locator("[\\@click*=\"selectScenario('RETIREMENT')\"]").click()
        page.wait_for_url("**/questions/", timeout=10_000)
        assert "/questions/" in page.url

    def test_page_uses_mobile_viewport(self, page: Page, app_url: str):
        page.goto(app_url + "/")
        viewport = page.viewport_size
        assert viewport["width"] == 375
        assert viewport["height"] == 667

    def test_no_horizontal_scroll(self, page: Page, app_url: str):
        page.goto(app_url + "/")
        page.wait_for_load_state("networkidle")
        scroll_width = page.evaluate("document.body.scrollWidth")
        client_width = page.evaluate("document.body.clientWidth")
        assert scroll_width <= client_width + 5, (
            f"Horizontal scroll detected: scrollWidth={scroll_width}, clientWidth={client_width}"
        )
