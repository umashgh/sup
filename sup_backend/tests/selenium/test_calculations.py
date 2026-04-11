"""
Calculation accuracy tests.

Tests the calculate API endpoint directly (POST /api/scenarios/calculate/)
with known fixed inputs and asserts deterministic expected outputs.
No Selenium/browser needed — uses requests against the live_server.

Coverage:
- FOUNDER: runway, available_cash, bootstrap_capital field
- RETIREMENT: corpus_gap, comfort_runway, required_corpus
- TERMINATION: severance added to available_cash
- HALF_FIRE: part-time income reduces net burn → longer runway
- R2I: part-time income offsets burn
- STANDARD tier (FOUNDER): chart_data has 21 data points (Year 0-20)
- RETIREMENT STANDARD: gratuity raises final_corpus when provided
"""
import json

import pytest
import requests as _requests

pytestmark = pytest.mark.django_db(transaction=True)


# ---------------------------------------------------------------------------
# Session helper
# ---------------------------------------------------------------------------

class APISession:
    """
    Thin wrapper around requests.Session that handles guest authentication
    and CSRF for the Django / DRF backend.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = _requests.Session()
        self._authenticated = False

    def _ensure_csrf(self):
        """Fetch a page to get the CSRF cookie if we don't have one yet."""
        if not self.session.cookies.get("csrftoken"):
            self.session.get(f"{self.base_url}/accounts/login/")

    def authenticate_as_guest(self):
        """Create a guest session (GET /start/)."""
        self._ensure_csrf()
        self.session.get(f"{self.base_url}/start/", allow_redirects=True)
        self._authenticated = True

    def _headers(self):
        csrf = self.session.cookies.get("csrftoken", "")
        return {
            "X-CSRFToken": csrf,
            "Referer": self.base_url,
            "Content-Type": "application/json",
        }

    def post(self, path: str, data: dict) -> dict:
        url = f"{self.base_url}{path}"
        resp = self.session.post(url, json=data, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def select_scenario(self, scenario_type: str) -> dict:
        return self.post("/api/scenarios/select/", {"scenario_type": scenario_type})

    def calculate(self, user_data: dict) -> dict:
        return self.post("/api/scenarios/calculate/", {"data": user_data})

    def advance_tier(self) -> dict:
        return self.post("/api/scenarios/advance-tier/", {})


# ---------------------------------------------------------------------------
# Shared minimal user_data builders
# ---------------------------------------------------------------------------

def _base_data(monthly_expenses=80000, monthly_needs=48000,
               living_total=2_000_000, security_total=1_000_000,
               passive_monthly=0, emergency_fund_months=6,
               **scenario_overrides):
    """Build a minimal QUICK tier user_data dict."""
    return {
        "scenario": scenario_overrides,
        "family": {
            "monthly_expenses": monthly_expenses,
            "monthly_needs": monthly_needs,
            "monthly_wants": monthly_expenses - monthly_needs,
            "one_time_expenses": 0,
        },
        "assets": {
            "living_total": living_total,
            "security_total": security_total,
        },
        "income": {"passive_monthly": passive_monthly},
        "profile": {"emergency_fund_months": emergency_fund_months},
    }


def _standard_data(monthly_expenses=80000, liquid=1_200_000, semi_liquid=800_000,
                   growth=1_500_000, property_val=0,
                   passive_monthly=0, emergency_fund_months=6,
                   **scenario_overrides):
    """Build a STANDARD tier user_data dict (uses split asset buckets)."""
    return {
        "scenario": scenario_overrides,
        "family": {
            "monthly_expenses": monthly_expenses,
            "monthly_needs": monthly_expenses * 0.6,
            "monthly_wants": monthly_expenses * 0.4,
            "one_time_expenses": 0,
            "kids_count": 0,
        },
        "assets": {
            "liquid": liquid,
            "semi_liquid": semi_liquid,
            "growth": growth,
            "property": property_val,
        },
        "income": {"passive_monthly": passive_monthly},
        "profile": {"emergency_fund_months": emergency_fund_months},
    }


# ---------------------------------------------------------------------------
# QUICK tier expected value calculations (mirrors calculator logic exactly)
# ---------------------------------------------------------------------------

def _quick_expected(monthly_expenses, monthly_needs, living_total, security_total,
                    passive_monthly=0, emergency_fund_months=6,
                    severance=0, parttime=0):
    """
    Mirror the QUICK-tier runway formula from the calculator code.
    Returns (available_cash, comfort_runway_months, austerity_runway_months).
    """
    total_assets = living_total + security_total
    survival_burn = monthly_needs
    comfort_burn = monthly_expenses
    emergency_fund_lock = survival_burn * emergency_fund_months
    available_cash = max(0, total_assets + severance - emergency_fund_lock)
    net_comfort = max(0, comfort_burn - passive_monthly - parttime)
    net_survival = max(0, survival_burn - passive_monthly - parttime)
    comfort_runway = available_cash / net_comfort if net_comfort > 0 else None
    austerity_runway = available_cash / net_survival if net_survival > 0 else None
    return available_cash, comfort_runway, austerity_runway


# ---------------------------------------------------------------------------
# FOUNDER tests
# ---------------------------------------------------------------------------

class TestFounderCalculation:
    """
    Known inputs:
      expenses=₹80k/mo, needs=₹48k, living=₹20L, security=₹10L,
      passive=0, emergency=6 months, venture_bootstrapped=False

    Expected:
      total_assets = ₹30L
      emergency_fund_lock = 48k × 6 = ₹2.88L
      available_cash = ₹30L - ₹2.88L = ₹27.12L
      comfort_runway = 2,712,000 / 80,000 = 33.9 months
      austerity_runway = 2,712,000 / 48,000 = 56.5 months
    """
    EXPENSES = 80_000
    NEEDS = 48_000
    LIVING = 2_000_000
    SECURITY = 1_000_000
    EXPECTED_AVAILABLE, EXPECTED_COMFORT, EXPECTED_AUSTERITY = _quick_expected(
        EXPENSES, NEEDS, LIVING, SECURITY
    )  # 2_712_000, 33.9, 56.5

    def test_available_cash(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
        )
        result = api.calculate(data)
        assert result.get("results"), f"No results in response: {result}"
        r = result["results"]
        assert r["available_cash"] == pytest.approx(self.EXPECTED_AVAILABLE, abs=1), (
            f"available_cash {r['available_cash']} ≠ {self.EXPECTED_AVAILABLE}"
        )

    def test_comfort_runway_within_tolerance(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
        )
        result = api.calculate(data)
        r = result["results"]
        assert r["comfort_runway_months"] == pytest.approx(self.EXPECTED_COMFORT, abs=2), (
            f"comfort_runway_months {r['comfort_runway_months']} "
            f"not within ±2 of {self.EXPECTED_COMFORT}"
        )

    def test_bootstrap_capital_in_results_when_bootstrapped(self, live_server):
        """
        When venture_bootstrapped=True and bootstrap_capital is provided,
        the results dict must include bootstrap_capital equal to the input value.
        """
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            venture_bootstrapped=True, bootstrap_capital=500_000,
        )
        result = api.calculate(data)
        r = result["results"]
        assert "bootstrap_capital" in r, (
            "bootstrap_capital key missing from FOUNDER results"
        )
        assert r["bootstrap_capital"] == pytest.approx(500_000, abs=1), (
            f"bootstrap_capital {r['bootstrap_capital']} ≠ 500000"
        )

    def test_bootstrap_zero_when_not_bootstrapped(self, live_server):
        """venture_bootstrapped=False → bootstrap_capital=0 in results."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            venture_bootstrapped=False,
        )
        result = api.calculate(data)
        r = result["results"]
        assert r.get("bootstrap_capital", 0) == 0


# ---------------------------------------------------------------------------
# RETIREMENT tests
# ---------------------------------------------------------------------------

class TestRetirementCalculation:
    """
    Known inputs:
      expenses=₹60k/mo, needs=₹36k, living=₹30L, security=₹20L,
      current_age=35, retirement_age=60, life_expectancy=85

    Expected:
      required_corpus = 60k × 12 × 25 = ₹1.8Cr
      current_corpus = ₹50L
      corpus_gap = ₹1.3Cr
      years_to_retirement = 25
      available_cash = 50L - 36k×6 = 50L - 2.16L = ₹47.84L
      comfort_runway ≈ 4,784,000 / 60,000 = 79.7 months
    """
    EXPENSES = 60_000
    NEEDS = 36_000
    LIVING = 3_000_000
    SECURITY = 2_000_000
    EXPECTED_CORPUS = 60_000 * 12 * 25  # 18_000_000
    EXPECTED_AVAILABLE, EXPECTED_COMFORT, _ = _quick_expected(
        EXPENSES, NEEDS, LIVING, SECURITY
    )

    def test_required_corpus(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("RETIREMENT")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            current_age=35, retirement_age=60, life_expectancy=85,
        )
        result = api.calculate(data)
        r = result["results"]
        assert r["required_corpus"] == pytest.approx(self.EXPECTED_CORPUS, abs=1), (
            f"required_corpus {r['required_corpus']} ≠ {self.EXPECTED_CORPUS}"
        )

    def test_corpus_gap(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("RETIREMENT")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            current_age=35, retirement_age=60, life_expectancy=85,
        )
        result = api.calculate(data)
        r = result["results"]
        current_corpus = self.LIVING + self.SECURITY
        expected_gap = max(0, self.EXPECTED_CORPUS - current_corpus)
        assert r["corpus_gap"] == pytest.approx(expected_gap, abs=1)

    def test_available_cash_positive(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("RETIREMENT")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            current_age=35, retirement_age=60, life_expectancy=85,
        )
        result = api.calculate(data)
        r = result["results"]
        assert r["available_cash"] > 0

    def test_comfort_runway_within_tolerance(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("RETIREMENT")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            current_age=35, retirement_age=60, life_expectancy=85,
        )
        result = api.calculate(data)
        r = result["results"]
        assert r["comfort_runway_months"] == pytest.approx(self.EXPECTED_COMFORT, abs=2)


# ---------------------------------------------------------------------------
# TERMINATION tests
# ---------------------------------------------------------------------------

class TestTerminationCalculation:
    """
    Known inputs:
      expenses=₹60k/mo, needs=₹36k, living=₹20L, security=₹10L,
      severance=₹12L, passive=0, emergency=6 months

    Expected:
      available_cash = (20L+10L) + 12L - 36k×6 = 42L - 2.16L = ₹39.84L
      comfort_runway = 3,984,000 / 60,000 = 66.4 months
    """
    EXPENSES = 60_000
    NEEDS = 36_000
    LIVING = 2_000_000
    SECURITY = 1_000_000
    SEVERANCE = 1_200_000
    EXPECTED_AVAILABLE, EXPECTED_COMFORT, EXPECTED_AUSTERITY = _quick_expected(
        EXPENSES, NEEDS, LIVING, SECURITY, severance=SEVERANCE
    )

    def test_severance_added_to_available_cash(self, live_server):
        """
        Termination calculator adds severance to available funds.
        available_cash must be larger than if severance were 0.
        """
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("TERMINATION")

        data_with = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            severance_lumpsum=self.SEVERANCE,
        )
        data_without = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            severance_lumpsum=0,
        )

        result_with = api.calculate(data_with)
        result_without = api.calculate(data_without)

        cash_with = result_with["results"]["available_cash"]
        cash_without = result_without["results"]["available_cash"]

        assert cash_with > cash_without, (
            f"Severance should increase available_cash: "
            f"with={cash_with}, without={cash_without}"
        )
        assert cash_with == pytest.approx(self.EXPECTED_AVAILABLE, abs=1), (
            f"available_cash with severance {cash_with} ≠ {self.EXPECTED_AVAILABLE}"
        )

    def test_comfort_runway_within_tolerance(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("TERMINATION")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            severance_lumpsum=self.SEVERANCE,
        )
        result = api.calculate(data)
        r = result["results"]
        assert r["comfort_runway_months"] == pytest.approx(self.EXPECTED_COMFORT, abs=2)

    def test_severance_key_present_in_results(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("TERMINATION")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            severance_lumpsum=self.SEVERANCE,
        )
        result = api.calculate(data)
        r = result["results"]
        assert "severance_lumpsum" in r
        assert r["severance_lumpsum"] == pytest.approx(self.SEVERANCE, abs=1)


# ---------------------------------------------------------------------------
# HALF_FIRE tests
# ---------------------------------------------------------------------------

class TestHalfFireCalculation:
    """
    Known inputs:
      expenses=₹60k/mo, needs=₹36k, living=₹30L, security=₹10L,
      parttime=₹20k/mo, passive=₹5k/mo, emergency=6 months

    Expected:
      available_cash = 40L - 36k×6 = 40L - 2.16L = ₹37.84L
      net_comfort_burn = 60k - 5k - 20k = 35k
      comfort_runway = 3,784,000 / 35,000 = 108.1 months
    """
    EXPENSES = 60_000
    NEEDS = 36_000
    LIVING = 3_000_000
    SECURITY = 1_000_000
    PARTTIME = 20_000
    PASSIVE = 5_000
    EXPECTED_AVAILABLE, EXPECTED_COMFORT, EXPECTED_AUSTERITY = _quick_expected(
        EXPENSES, NEEDS, LIVING, SECURITY, PASSIVE, 6, parttime=PARTTIME
    )

    def test_parttime_income_extends_runway(self, live_server):
        """Part-time income should produce a longer runway than with no income."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("HALF_FIRE")

        data_with = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            passive_monthly=self.PASSIVE,
            parttime_monthly_income=self.PARTTIME,
        )
        data_without = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            passive_monthly=0,
            parttime_monthly_income=0,
        )
        result_with = api.calculate(data_with)
        result_without = api.calculate(data_without)

        runway_with = result_with["results"]["comfort_runway_months"]
        runway_without = result_without["results"]["comfort_runway_months"]

        assert runway_with > runway_without, (
            f"Part-time income should extend comfort runway: "
            f"with={runway_with}, without={runway_without}"
        )

    def test_comfort_runway_within_tolerance(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("HALF_FIRE")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            passive_monthly=self.PASSIVE,
            parttime_monthly_income=self.PARTTIME,
        )
        result = api.calculate(data)
        r = result["results"]
        assert r["comfort_runway_months"] == pytest.approx(self.EXPECTED_COMFORT, abs=2)

    def test_available_cash_positive(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("HALF_FIRE")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            passive_monthly=self.PASSIVE,
            parttime_monthly_income=self.PARTTIME,
        )
        result = api.calculate(data)
        assert result["results"]["available_cash"] > 0


# ---------------------------------------------------------------------------
# R2I tests
# ---------------------------------------------------------------------------

class TestR2ICalculation:
    """
    Known inputs:
      expenses=₹70k/mo, needs=₹42k, living=₹40L, security=₹10L,
      india_work_income=₹15k/mo, passive=0, emergency=6 months

    Expected:
      available_cash = 50L - 42k×6 = 50L - 2.52L = ₹47.48L
      net_comfort_burn = max(0, 70k - 0 - 15k) = 55k
      comfort_runway = 4,748,000 / 55,000 ≈ 86.3 months
    """
    EXPENSES = 70_000
    NEEDS = 42_000
    LIVING = 4_000_000
    SECURITY = 1_000_000
    PARTTIME = 15_000
    EXPECTED_AVAILABLE, EXPECTED_COMFORT, _ = _quick_expected(
        EXPENSES, NEEDS, LIVING, SECURITY, parttime=PARTTIME
    )

    def test_available_cash_positive(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("R2I")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            parttime_monthly_income=self.PARTTIME,
        )
        result = api.calculate(data)
        assert result["results"]["available_cash"] > 0

    def test_comfort_runway_within_tolerance(self, live_server):
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("R2I")

        data = _base_data(
            monthly_expenses=self.EXPENSES, monthly_needs=self.NEEDS,
            living_total=self.LIVING, security_total=self.SECURITY,
            parttime_monthly_income=self.PARTTIME,
        )
        result = api.calculate(data)
        r = result["results"]
        assert r["comfort_runway_months"] == pytest.approx(self.EXPECTED_COMFORT, abs=2)


# ---------------------------------------------------------------------------
# STANDARD tier — chart_data and 20-year projection
# ---------------------------------------------------------------------------

class TestStandardTierChartData:
    """
    STANDARD tier results must include chart_data with 21 data points
    (Year 0 through Year 20, inclusive).
    """

    def test_founder_standard_chart_data_has_21_points(self, live_server):
        """
        After advancing to STANDARD tier (tier 2), the calculate endpoint
        must return chart_data with exactly 21 year entries.
        """
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")

        # Advance to tier 2
        api.advance_tier()

        standard_data = _standard_data(
            monthly_expenses=80_000,
            liquid=1_200_000,
            semi_liquid=800_000,
            growth=2_000_000,
            property_val=0,
            venture_bootstrapped=False,
            bootstrap_capital=0,
        )
        result = api.calculate(standard_data)
        assert result.get("results"), f"No results: {result}"
        r = result["results"]

        assert "chart_data" in r, "chart_data missing from STANDARD tier results"
        cd = r["chart_data"]
        assert len(cd["years"]) == 21, (
            f"Expected 21 chart data points (Year 0-20), got {len(cd['years'])}"
        )
        assert len(cd["assets"]) == 21
        assert len(cd["needs"]) == 21
        assert len(cd["incomes"]) == 21

    def test_chart_years_labeled_correctly(self, live_server):
        """chart_data['years'] must be ['Year 0', 'Year 1', ..., 'Year 20']."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        standard_data = _standard_data(monthly_expenses=80_000)
        result = api.calculate(standard_data)
        years = result["results"]["chart_data"]["years"]
        assert years[0] == "Year 0"
        assert years[-1] == "Year 20"

    def test_standard_results_include_sustainability_flag(self, live_server):
        """STANDARD tier results must include a boolean 'sustainable' key."""
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("FOUNDER")
        api.advance_tier()

        standard_data = _standard_data(monthly_expenses=80_000)
        result = api.calculate(standard_data)
        r = result["results"]
        assert "sustainable" in r, "sustainable key missing from STANDARD results"
        assert isinstance(r["sustainable"], bool)


# ---------------------------------------------------------------------------
# RETIREMENT STANDARD — gratuity injection
# ---------------------------------------------------------------------------

class TestRetirementGratuity:
    """
    The STANDARD retirement calculator injects gratuity as a lump-sum
    into the liquid bucket at the year of retirement. With a large enough
    gratuity, the final_corpus should be measurably higher than without it.
    """

    def test_gratuity_increases_final_corpus(self, live_server):
        """
        final_corpus with gratuity_lumpsum=₹20L > final_corpus without.
        """
        api = APISession(live_server.url)
        api.authenticate_as_guest()
        api.select_scenario("RETIREMENT")
        api.advance_tier()

        base = dict(
            monthly_expenses=60_000,
            liquid=1_200_000, semi_liquid=800_000,
            growth=1_000_000, property_val=0,
            current_age=40, retirement_age=65, life_expectancy=85,
        )

        data_with = _standard_data(**base, gratuity_lumpsum=2_000_000)
        data_without = _standard_data(**base, gratuity_lumpsum=0)

        result_with = api.calculate(data_with)
        result_without = api.calculate(data_without)

        corpus_with = result_with["results"]["final_corpus"]
        corpus_without = result_without["results"]["final_corpus"]

        assert corpus_with > corpus_without, (
            f"Gratuity should increase final_corpus: "
            f"with={corpus_with:.0f}, without={corpus_without:.0f}"
        )
