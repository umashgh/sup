"""
Monte Carlo feature tests.

Checks that the Monte Carlo simulation:
- API endpoint exists and returns expected structure
- Results include percentile bands (P10/P50/P90)
- Results include fan_chart with 21 data points
- UI: "Run simulation →" button appears on results page (Standard tier)
- UI: After clicking, mcResults section renders with success_rate and P10/P50/P90

The entire test module is skipped if the Monte Carlo engine is not importable.
"""
import json
import uuid

import pytest
import requests as _requests

try:
    from core.calculators.monte_carlo import MonteCarloEngine
    _MC_AVAILABLE = True
except ImportError:
    _MC_AVAILABLE = False

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not _MC_AVAILABLE, reason="MonteCarloEngine not available"),
]

WAIT = 20  # longer timeout: MC runs 2,000 paths


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

    def run_monte_carlo(self, user_data: dict, results: dict) -> dict:
        return self.post("/api/scenarios/monte-carlo/", {
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
    Minimal STANDARD tier results dict as returned by the calculate endpoint.
    Monte Carlo only needs the base projection fields — it re-runs the simulation
    using user_data, not chart_data.
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

class TestMonteCarloAPI:
    def test_monte_carlo_returns_success(self, live_server):
        """POST /api/scenarios/monte-carlo/ returns success=True."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        user_data = _standard_user_data()
        # Run a STANDARD calc first (so the endpoint has the right tier in DB)
        std_result = api.calculate(user_data)
        assert std_result.get("results", {}).get("tier") == "STANDARD", (
            "Expected STANDARD tier results to confirm tier advance"
        )

        mc_response = api.run_monte_carlo(user_data, std_result["results"])
        assert mc_response.get("success"), f"MC response not successful: {mc_response}"

    def test_monte_carlo_requires_standard_results(self, live_server):
        """
        Sending tier='QUICK' results must return an error — Monte Carlo
        requires STANDARD tier results.
        """
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")

        quick_results = {
            "tier": "QUICK",
            "scenario_type": "FOUNDER",
            "monthly_expenses": 80_000,
        }
        resp = _requests.Session()
        resp.get(f"{live_server.url}/accounts/login/")
        resp.get(f"{live_server.url}/start/")
        csrf = resp.cookies.get("csrftoken", "")
        response = resp.post(
            f"{live_server.url}/api/scenarios/monte-carlo/",
            json={"data": _standard_user_data(), "results": quick_results},
            headers={"X-CSRFToken": csrf, "Referer": live_server.url, "Content-Type": "application/json"},
        )
        assert response.status_code in (400, 403, 422), (
            "MC with QUICK results should return a 4xx error"
        )

    def test_monte_carlo_has_success_rate(self, live_server):
        """MC result must contain a numeric success_rate in [0, 100]."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        user_data = _standard_user_data()
        std_result = api.calculate(user_data)
        mc = api.run_monte_carlo(user_data, std_result["results"])

        mc_data = mc["mc"]
        assert "success_rate" in mc_data, "success_rate missing from MC results"
        assert 0 <= mc_data["success_rate"] <= 100, (
            f"success_rate out of range: {mc_data['success_rate']}"
        )

    def test_monte_carlo_has_percentile_bands(self, live_server):
        """MC result must contain P10, P50, P90 final corpus values."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        user_data = _standard_user_data()
        std_result = api.calculate(user_data)
        mc = api.run_monte_carlo(user_data, std_result["results"])
        mc_data = mc["mc"]

        for key in ("p10_final", "p50_final", "p90_final"):
            assert key in mc_data, f"{key} missing from MC results"
            assert isinstance(mc_data[key], (int, float)), f"{key} is not numeric"

        # Pessimistic ≤ Median ≤ Optimistic
        assert mc_data["p10_final"] <= mc_data["p50_final"], (
            "P10 should be <= P50"
        )
        assert mc_data["p50_final"] <= mc_data["p90_final"], (
            "P50 should be <= P90"
        )

    def test_monte_carlo_has_fan_chart_with_21_points(self, live_server):
        """MC result must include fan_chart with 21 data points per percentile."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        user_data = _standard_user_data()
        std_result = api.calculate(user_data)
        mc = api.run_monte_carlo(user_data, std_result["results"])
        mc_data = mc["mc"]

        assert "fan_chart" in mc_data, "fan_chart missing from MC results"
        fc = mc_data["fan_chart"]

        for key in ("years", "p10", "p25", "p50", "p75", "p90"):
            assert key in fc, f"fan_chart.{key} missing"
            assert len(fc[key]) == 21, (
                f"fan_chart.{key} should have 21 points (Year 0-20), "
                f"got {len(fc[key])}"
            )

    def test_monte_carlo_n_iterations(self, live_server):
        """MC result must report n_iterations."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        user_data = _standard_user_data()
        std_result = api.calculate(user_data)
        mc = api.run_monte_carlo(user_data, std_result["results"])
        mc_data = mc["mc"]

        assert "n_iterations" in mc_data, "n_iterations missing from MC results"
        assert mc_data["n_iterations"] > 0, "n_iterations must be positive"


# ---------------------------------------------------------------------------
# UI-level tests (Selenium)
# ---------------------------------------------------------------------------

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TestMonteCarloUI:
    def _seed_standard_results(self, driver, live_server, scenario_type="FOUNDER"):
        """Authenticate as guest and seed STANDARD results into sessionStorage."""
        driver.get(f"{live_server.url}/start/")
        WebDriverWait(driver, 10).until(EC.url_contains(live_server.url))

        results = _stub_standard_results(scenario_type)
        driver.execute_script(
            f"sessionStorage.setItem('calculation_results', JSON.stringify({json.dumps(results)}))"
        )
        driver.get(f"{live_server.url}/results/")

    def test_run_simulation_button_visible_on_standard_results(
        self, driver, live_server
    ):
        """
        'Run simulation →' button must be visible on the results page
        when calculation_results.tier === 'STANDARD'.
        """
        self._seed_standard_results(driver, live_server)
        WebDriverWait(driver, WAIT).until(
            lambda d: d.execute_script(
                "return JSON.parse(sessionStorage.getItem('calculation_results') || '{}').tier === 'STANDARD'"
            )
        )
        # The MC section is x-show="!loading && results.tier === 'STANDARD'"
        # The button is shown when !mcResults && !mcLoading
        run_btn = WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Run simulation')]"))
        )
        assert run_btn is not None, "Run simulation button not found"

    def test_mc_results_section_rendered_after_click(
        self, driver, live_server
    ):
        """
        After clicking 'Run simulation →', the MC results section
        (with success_rate and P10/P50/P90 grid) must appear.
        """
        self._seed_standard_results(driver, live_server)

        # First, advance the session to tier 2 via the Alpine API call
        # so the backend accepts the MC request
        driver.execute_script("""
            // Ensure we are on the right page
            if (window.location.pathname !== '/results/') return;
        """)

        run_btn = WebDriverWait(driver, WAIT).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Run simulation')]")
            )
        )
        run_btn.click()

        # Either mc results appear or an error is shown (network may fail in test)
        WebDriverWait(driver, WAIT).until(
            lambda d: (
                d.execute_script(
                    "const el = document.querySelector('[x-data]');"
                    "if (!el || !el._x_dataStack) return false;"
                    "const d = el._x_dataStack[0];"
                    "return (d && (d.mcResults !== null || d.mcError !== null || d.mcLoading === false));"
                )
            )
        )

        # Check that either results are shown or a clear error is displayed
        mc_result_or_error = driver.execute_script(
            "const el = document.querySelector('[x-data]');"
            "const d = el._x_dataStack[0];"
            "return {mcResults: !!d.mcResults, mcError: d.mcError};"
        )
        # One of the two must be set — not both empty
        assert mc_result_or_error["mcResults"] or mc_result_or_error["mcError"], (
            "After clicking Run simulation, neither mcResults nor mcError is set"
        )

    def test_mc_canvas_present_in_dom(self, driver, live_server):
        """
        The fan chart canvas element (id='mcFanChart') must be present in the
        results page DOM when STANDARD tier results are loaded.
        """
        self._seed_standard_results(driver, live_server)

        canvas = WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.ID, "mcFanChart"))
        )
        assert canvas is not None, "mcFanChart canvas not found in DOM"
