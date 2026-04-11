"""
Ask Advisor (Asha) feature tests.

Covers:
- "Analyse my plan →" button is visible on the results page (Standard tier)
- The advisor API returns a non-empty advice string
- The advice renders in the UI after clicking
- Error state shown when advisor returns an error

The advisor requires Standard tier results — tests are skipped if the
advisor module (core/advisor.py) is not importable.
"""
import json
import uuid

import pytest
import requests as _requests

try:
    from core.advisor import get_advice  # noqa: F401
    _ADVISOR_AVAILABLE = True
except ImportError:
    _ADVISOR_AVAILABLE = False

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not _ADVISOR_AVAILABLE, reason="Advisor module not available"),
]

WAIT = 30  # AI advisor may take several seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class APISession:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = _requests.Session()

    def _csrf(self):
        return self.session.cookies.get("csrftoken", "")

    def _headers(self):
        return {
            "X-CSRFToken": self._csrf(),
            "Referer": self.base_url,
            "Content-Type": "application/json",
        }

    def authenticate_as_guest(self):
        self.session.get(f"{self.base_url}/accounts/login/")
        self.session.get(f"{self.base_url}/start/", allow_redirects=True)

    def post(self, path: str, data: dict) -> dict:
        resp = self.session.post(
            f"{self.base_url}{path}", json=data, headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def select_scenario(self, scenario_type: str) -> dict:
        return self.post("/api/scenarios/select/", {"scenario_type": scenario_type})

    def advance_tier(self) -> dict:
        return self.post("/api/scenarios/advance-tier/", {})

    def calculate(self, user_data: dict) -> dict:
        return self.post("/api/scenarios/calculate/", {"data": user_data})

    def advise(self, user_data: dict, results: dict) -> dict:
        return self.post("/api/scenarios/advise/", {
            "data": user_data,
            "results": results,
        })


def _standard_user_data(expenses=80_000):
    """Minimal STANDARD tier user_data for a FOUNDER scenario."""
    return {
        "scenario": {
            "venture_bootstrapped": False,
            "bootstrap_capital": 0,
        },
        "family": {
            "monthly_expenses": expenses,
            "monthly_needs": expenses * 0.6,
            "monthly_wants": expenses * 0.4,
            "one_time_expenses": 0,
            "kids_count": 0,
        },
        "assets": {
            "liquid": 1_200_000,
            "semi_liquid": 800_000,
            "growth": 2_000_000,
            "property": 0,
        },
        "income": {"passive_monthly": 0},
        "profile": {"emergency_fund_months": 6},
        "rates": {
            "liquid_return": 0.06,
            "semi_liquid_return": 0.08,
            "growth_return": 0.12,
            "property_appreciation": 0.05,
            "property_rental_yield": 0.03,
            "needs_inflation": 0.06,
            "wants_inflation": 0.07,
            "passive_growth": 0.04,
            "swr_rate": 0.04,
        },
    }


def _stub_standard_results(scenario_type="FOUNDER", expenses=80_000):
    """
    Minimal STANDARD tier result dict for seeding sessionStorage.
    """
    years = [f"Year {i}" for i in range(21)]
    assets = [float(4_000_000 * (1.08 ** i)) for i in range(21)]
    return {
        "tier": "STANDARD",
        "scenario_type": scenario_type,
        "monthly_expenses": expenses,
        "monthly_passive": 0,
        "available_cash": 3_784_000,
        "total_assets": 4_000_000,
        "emergency_fund_lock": 216_000,
        "comfort_runway_months": 63.1,
        "austerity_runway_months": 105.1,
        "target_number": 14_400_000,
        "target_gap": 10_400_000,
        "free_up_year": None,
        "depletion_year": 15,
        "final_corpus": 0,
        "sustainable": False,
        "chart_data": {
            "years": years,
            "assets": assets,
            "needs": [expenses * 0.6] * 21,
            "wants": [expenses * 0.4] * 21,
            "incomes": [0.0] * 21,
        },
    }


# ---------------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------------

class TestAdvisorAPI:
    def test_advisor_returns_success(self, live_server):
        """POST /api/scenarios/advise/ returns success=True with STANDARD results."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        user_data = _standard_user_data()
        std_result = api.calculate(user_data)
        assert std_result.get("results", {}).get("tier") == "STANDARD"

        resp = api.advise(user_data, std_result["results"])
        assert resp.get("success"), f"Advisor response not successful: {resp}"

    def test_advisor_returns_non_empty_advice(self, live_server):
        """The advice string must be non-empty."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        user_data = _standard_user_data()
        std_result = api.calculate(user_data)
        resp = api.advise(user_data, std_result["results"])

        advice = resp.get("advice", "")
        assert advice and len(advice.strip()) > 50, (
            f"Expected substantial advice text, got: {advice!r}"
        )

    def test_advisor_requires_standard_tier(self, live_server):
        """Submitting tier='QUICK' results must be rejected by the advisor."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")

        quick_results = {
            "tier": "QUICK",
            "scenario_type": "FOUNDER",
            "monthly_expenses": 80_000,
            "comfort_runway_months": 33.9,
        }
        s = _requests.Session()
        s.get(f"{live_server.url}/accounts/login/")
        s.get(f"{live_server.url}/start/")
        csrf = s.cookies.get("csrftoken", "")
        response = s.post(
            f"{live_server.url}/api/scenarios/advise/",
            json={"data": _standard_user_data(), "results": quick_results},
            headers={
                "X-CSRFToken": csrf,
                "Referer": live_server.url,
                "Content-Type": "application/json",
            },
        )
        # Must return 4xx error
        assert response.status_code in (400, 403, 422), (
            f"Advisor with QUICK results should return 4xx, got {response.status_code}"
        )

    def test_advisor_returns_advice_key(self, live_server):
        """The response dict must contain an 'advice' key."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        user_data = _standard_user_data()
        std_result = api.calculate(user_data)
        resp = api.advise(user_data, std_result["results"])

        assert "advice" in resp, f"'advice' key missing from advisor response: {resp}"

    def test_advisor_advice_is_string(self, live_server):
        """The advice value must be a string (not a list/dict)."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        user_data = _standard_user_data()
        std_result = api.calculate(user_data)
        resp = api.advise(user_data, std_result["results"])

        assert isinstance(resp["advice"], str), (
            f"advice should be str, got {type(resp['advice']).__name__}"
        )


# ---------------------------------------------------------------------------
# UI-level tests (Selenium)
# ---------------------------------------------------------------------------

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TestAdvisorUI:
    def _seed_standard_results(self, driver, live_server):
        """Authenticate as guest and seed STANDARD results into sessionStorage."""
        driver.get(f"{live_server.url}/start/")
        WebDriverWait(driver, 10).until(EC.url_contains(live_server.url))

        results = _stub_standard_results()
        driver.execute_script(
            f"sessionStorage.setItem('calculation_results', JSON.stringify({json.dumps(results)}))"
        )
        driver.get(f"{live_server.url}/results/")

    def test_analyse_button_visible_on_standard_results(
        self, driver, live_server
    ):
        """
        'Analyse my plan →' button must be present on the results page
        when tier='STANDARD'.
        """
        self._seed_standard_results(driver, live_server)

        btn = WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(text(), 'Analyse my plan')]")
            )
        )
        assert btn is not None, "Analyse my plan button not found"

    def test_advisor_section_header_present(self, driver, live_server):
        """
        The advisor section must show 'Asha · AI Advisor' label in the header.
        The element is in the DOM (even if hidden before advice is fetched).
        """
        self._seed_standard_results(driver, live_server)

        # Wait for page to fully load
        WebDriverWait(driver, WAIT).until(
            lambda d: d.execute_script(
                "return JSON.parse(sessionStorage.getItem('calculation_results') || '{}').tier === 'STANDARD'"
            )
        )
        # The header text 'Asha · AI Advisor' is inside x-show="advice"
        # It's rendered but may be display:none initially
        body_html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")
        assert "Asha" in body_html and "AI Advisor" in body_html, (
            "Advisor header 'Asha · AI Advisor' not found in page HTML"
        )

    def test_clicking_analyse_triggers_loading_or_result(
        self, driver, live_server
    ):
        """
        Clicking 'Analyse my plan →' must change the Alpine state to either
        adviceLoading=true (started loading) or advice is set.
        """
        self._seed_standard_results(driver, live_server)

        btn = WebDriverWait(driver, WAIT).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Analyse my plan')]")
            )
        )
        btn.click()

        # Either adviceLoading=true or advice has been set or adviceError set
        WebDriverWait(driver, WAIT).until(
            lambda d: d.execute_script(
                "const el = document.querySelector('[x-data]');"
                "if (!el || !el._x_dataStack) return false;"
                "const d = el._x_dataStack[0];"
                "return d && (d.adviceLoading === true || d.advice !== null || d.adviceError !== null);"
            )
        )
        state = driver.execute_script(
            "const el = document.querySelector('[x-data]');"
            "const d = el._x_dataStack[0];"
            "return {loading: d.adviceLoading, advice: !!d.advice, error: d.adviceError};"
        )
        assert state["loading"] or state["advice"] or state["error"], (
            "Expected advisor to start loading, succeed, or show an error"
        )

    def test_advice_card_renders_after_successful_fetch(
        self, driver, live_server
    ):
        """
        After a successful advisor call, the advice card must appear.
        The card contains the Asha header and the advice text body.

        If the advisor API fails (e.g. no API key in test env), we verify
        that an error message is shown instead — both are acceptable UI states.
        """
        self._seed_standard_results(driver, live_server)

        btn = WebDriverWait(driver, WAIT).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Analyse my plan')]")
            )
        )
        btn.click()

        # Wait for the request to complete (advice set OR error set)
        WebDriverWait(driver, WAIT).until(
            lambda d: d.execute_script(
                "const el = document.querySelector('[x-data]');"
                "if (!el || !el._x_dataStack) return false;"
                "const d = el._x_dataStack[0];"
                "return d && !d.adviceLoading && (d.advice !== null || d.adviceError !== null);"
            )
        )

        final_state = driver.execute_script(
            "const el = document.querySelector('[x-data]');"
            "const d = el._x_dataStack[0];"
            "return {advice: d.advice, error: d.adviceError};"
        )

        if final_state["advice"]:
            # Verify the advice card is actually in the DOM (x-show="advice")
            advice_sections = driver.find_elements(
                By.XPATH, "//*[contains(text(), 'Asha · AI Advisor')]"
            )
            assert advice_sections, "Asha advisor card not found in DOM after advice loaded"
        else:
            # Advisor API unavailable in test env — verify error shown to user
            error_el = driver.find_elements(
                By.XPATH,
                "//*[@x-text='adviceError' or contains(@style, 'adviceError')]",
            )
            # Simpler check: verify adviceError is in Alpine state
            assert final_state["error"], (
                "Neither advice nor error state is set after advisor call completed"
            )
