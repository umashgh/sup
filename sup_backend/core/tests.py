"""
Tests for core app — covering all recent changes:

  1. UserRatePreferences model (defaults, as_dict, as_pct_dict)
  2. Rate preferences API  (GET / PATCH)
  3. StandardBaseCalculator._load_rates() picks up user overrides
  4. SWR removed from projection income (no double-counting)
  5. QuickFounderCalculator runs without current_monthly_salary
  6. StandardFounderCalculator respects founder_salary_start_year
  7. kids_independence_year uses user-supplied kids_independence_age
  8. calculate_tier view injects rate prefs into user_data
"""

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User

from core.models import ScenarioProfile, UserRatePreferences
from core.calculators.base import StandardBaseCalculator
from core.calculators.quick.founder import QuickFounderCalculator
from core.calculators.standard.founder import StandardFounderCalculator
from finance.models import FamilyProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username="testuser"):
    return User.objects.create_user(username=username, password="pass")


def _base_standard_data(**overrides):
    """Minimal user_data dict that satisfies StandardBaseCalculator required fields."""
    data = {
        "family": {"monthly_expenses": 50000, "one_time_expenses": 0},
        "assets": {
            "liquid": 1_000_000,
            "semi_liquid": 500_000,
            "growth": 2_000_000,
            "property": 0,
        },
        "income": {"passive_monthly": 0},
        "profile": {"emergency_fund_months": 6},
        "scenario": {},
        "rates": {},
    }
    for k, v in overrides.items():
        if isinstance(v, dict) and k in data:
            data[k].update(v)
        else:
            data[k] = v
    return data


# ---------------------------------------------------------------------------
# 1. UserRatePreferences model
# ---------------------------------------------------------------------------

class UserRatePreferencesModelTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_defaults(self):
        prefs = UserRatePreferences.objects.create(user=self.user)
        self.assertEqual(float(prefs.liquid_return_pct), 6.0)
        self.assertEqual(float(prefs.semi_liquid_return_pct), 8.0)
        self.assertEqual(float(prefs.growth_return_pct), 12.0)
        self.assertEqual(float(prefs.property_appreciation_pct), 5.0)
        self.assertEqual(float(prefs.property_rental_yield_pct), 3.0)
        self.assertEqual(float(prefs.needs_inflation_pct), 6.0)
        self.assertEqual(float(prefs.wants_inflation_pct), 7.0)
        self.assertEqual(float(prefs.passive_growth_pct), 4.0)
        self.assertEqual(float(prefs.swr_rate_pct), 4.0)

    def test_as_dict_returns_decimals(self):
        prefs = UserRatePreferences.objects.create(user=self.user)
        d = prefs.as_dict()
        self.assertAlmostEqual(d["liquid_return"], 0.06)
        self.assertAlmostEqual(d["growth_return"], 0.12)
        self.assertAlmostEqual(d["needs_inflation"], 0.06)
        self.assertAlmostEqual(d["swr_rate"], 0.04)

    def test_as_pct_dict_returns_percentages(self):
        prefs = UserRatePreferences.objects.create(user=self.user)
        d = prefs.as_pct_dict()
        self.assertAlmostEqual(d["liquid_return_pct"], 6.0)
        self.assertAlmostEqual(d["growth_return_pct"], 12.0)

    def test_override_persists(self):
        prefs = UserRatePreferences.objects.create(user=self.user, growth_return_pct=15.0)
        prefs.refresh_from_db()
        self.assertAlmostEqual(float(prefs.growth_return_pct), 15.0)
        self.assertAlmostEqual(prefs.as_dict()["growth_return"], 0.15)

    def test_str(self):
        prefs = UserRatePreferences.objects.create(user=self.user)
        self.assertIn(self.user.username, str(prefs))


# ---------------------------------------------------------------------------
# 2. Rate preferences API
# ---------------------------------------------------------------------------

class RatePreferencesAPITests(TestCase):

    def setUp(self):
        self.user = make_user("apiuser")
        self.client = Client()
        self.client.force_login(self.user)
        FamilyProfile.objects.create(user=self.user)

    def test_get_returns_defaults(self):
        resp = self.client.get("/api/scenarios/rates/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("rates", data)
        self.assertAlmostEqual(data["rates"]["liquid_return_pct"], 6.0)
        self.assertAlmostEqual(data["rates"]["growth_return_pct"], 12.0)

    def test_patch_updates_fields(self):
        payload = {"growth_return_pct": 14.0, "needs_inflation_pct": 7.0}
        resp = self.client.patch(
            "/api/scenarios/rates/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertAlmostEqual(data["rates"]["growth_return_pct"], 14.0)
        self.assertAlmostEqual(data["rates"]["needs_inflation_pct"], 7.0)
        # unchanged field must still be default
        self.assertAlmostEqual(data["rates"]["liquid_return_pct"], 6.0)

    def test_patch_persists_to_db(self):
        self.client.patch(
            "/api/scenarios/rates/",
            data=json.dumps({"swr_rate_pct": 3.5}),
            content_type="application/json",
        )
        prefs = UserRatePreferences.objects.get(user=self.user)
        self.assertAlmostEqual(float(prefs.swr_rate_pct), 3.5)

    def test_patch_ignores_unknown_fields(self):
        resp = self.client.patch(
            "/api/scenarios/rates/",
            data=json.dumps({"hacker_field": 999}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        # Model must not have been changed
        prefs = UserRatePreferences.objects.get(user=self.user)
        self.assertAlmostEqual(float(prefs.growth_return_pct), 12.0)

    def test_unauthenticated_returns_403(self):
        anon = Client()
        resp = anon.get("/api/scenarios/rates/")
        self.assertIn(resp.status_code, [401, 403])


# ---------------------------------------------------------------------------
# 3. StandardBaseCalculator._load_rates() picks up user overrides
# ---------------------------------------------------------------------------

class _ConcreteStandardCalc(StandardBaseCalculator):
    """Minimal concrete subclass — no scenario-specific logic."""
    def _get_scenario_results(self):
        return {}
    def get_required_fields(self):
        return super().get_required_fields()


class LoadRatesTests(TestCase):

    def test_defaults_when_no_rates_key(self):
        data = _base_standard_data()
        del data["rates"]
        calc = _ConcreteStandardCalc(data)
        calc._load_rates()
        self.assertAlmostEqual(calc.GROWTH_RETURN, 0.12)
        self.assertAlmostEqual(calc.NEEDS_INFLATION, 0.06)

    def test_user_override_applied(self):
        data = _base_standard_data(rates={
            "growth_return": 0.15,
            "needs_inflation": 0.07,
        })
        calc = _ConcreteStandardCalc(data)
        calc._load_rates()
        self.assertAlmostEqual(calc.GROWTH_RETURN, 0.15)
        self.assertAlmostEqual(calc.NEEDS_INFLATION, 0.07)
        # un-overridden rate stays at default
        self.assertAlmostEqual(calc.LIQUID_RETURN, 0.06)

    def test_partial_override_leaves_others_intact(self):
        data = _base_standard_data(rates={"swr_rate": 0.035})
        calc = _ConcreteStandardCalc(data)
        calc._load_rates()
        self.assertAlmostEqual(calc.SWR_RATE, 0.035)
        self.assertAlmostEqual(calc.SEMI_LIQUID_RETURN, 0.08)


# ---------------------------------------------------------------------------
# 4. SWR removed from projection income
# ---------------------------------------------------------------------------

class ProjectionNoSWRIncomeTests(TestCase):

    def test_income_equals_passive_plus_scenario_only(self):
        """
        With no passive income and no scenario income, income_values should
        always be 0 (or only rental yield if property > 0). SWR must NOT
        appear in income_values.
        """
        data = _base_standard_data()
        data["income"]["passive_monthly"] = 0
        data["assets"]["property"] = 0  # no rental either
        calc = _ConcreteStandardCalc(data)
        calc.calculate()
        for val in calc.income_values:
            self.assertEqual(val, 0, msg=f"Expected 0 income, got {val}")

    def test_rental_income_appears_in_projection(self):
        """Property rental yield should still appear as income."""
        data = _base_standard_data()
        data["assets"]["property"] = 1_000_000
        data["income"]["passive_monthly"] = 0
        calc = _ConcreteStandardCalc(data)
        calc.calculate()
        # Year 0: 1_000_000 * 3% = 30_000
        expected_y0 = 1_000_000 * calc.PROPERTY_RENTAL_YIELD
        self.assertAlmostEqual(calc.income_values[0], expected_y0, delta=1)

    def test_swr_not_in_income_with_large_financial_assets(self):
        """
        Previously 4% of financial_assets would appear as income every year.
        With ₹1Cr in growth assets that would be ₹4L/yr; verify it is absent.
        """
        data = _base_standard_data()
        data["assets"]["growth"] = 10_000_000   # ₹1 Cr
        data["assets"]["property"] = 0
        data["income"]["passive_monthly"] = 0
        calc = _ConcreteStandardCalc(data)
        calc.calculate()
        old_swr_income = 10_000_000 * 0.04   # what old code would have added
        for val in calc.income_values:
            self.assertLess(
                val, old_swr_income,
                msg=f"Income {val} looks like it still contains SWR ({old_swr_income})"
            )

    def test_deficit_still_drawn_from_buckets(self):
        """Even with no income, the projection should draw from liquid assets."""
        data = _base_standard_data()
        data["income"]["passive_monthly"] = 0
        data["assets"]["liquid"] = 5_000_000
        data["assets"]["property"] = 0
        calc = _ConcreteStandardCalc(data)
        calc.calculate()
        # Assets should decline from year 0 due to expense drawdown
        self.assertLess(
            calc.assets_values[5], calc.assets_values[0],
            msg="Assets should decrease when income can't cover expenses"
        )


# ---------------------------------------------------------------------------
# 5. QuickFounderCalculator — no current_monthly_salary crash
# ---------------------------------------------------------------------------

class QuickFounderCalculatorTests(TestCase):

    def _make_data(self, **kwargs):
        base = {
            "family": {
                "monthly_expenses": 60000,
                "monthly_needs": 36000,
                "monthly_wants": 24000,
                "one_time_expenses": 0,
            },
            "assets": {"living_total": 2_000_000, "security_total": 3_000_000},
            "income": {"passive_monthly": 0},
            "profile": {"emergency_fund_months": 6},
            "scenario": {"venture_bootstrapped": False, "bootstrap_capital": 0},
        }
        base.update(kwargs)
        return base

    def test_runs_without_current_monthly_salary(self):
        """Field was read but unused — removing it must not break calculation."""
        data = self._make_data()
        calc = QuickFounderCalculator(data)
        result = calc.calculate()
        self.assertEqual(result["scenario_type"], "FOUNDER")
        self.assertIn("austerity_runway_months", result)

    def test_no_current_monthly_salary_key_in_result(self):
        data = self._make_data()
        result = QuickFounderCalculator(data).calculate()
        self.assertNotIn("current_monthly_salary", result)

    def test_bootstrap_capital_reduces_available_cash(self):
        data = self._make_data()
        data["scenario"]["venture_bootstrapped"] = True
        data["scenario"]["bootstrap_capital"] = 500_000
        result = QuickFounderCalculator(data).calculate()
        self.assertAlmostEqual(result["bootstrap_capital"], 500_000)

    def test_infinite_runway_when_passive_covers_all(self):
        data = self._make_data()
        data["income"]["passive_monthly"] = 100_000  # more than expenses
        result = QuickFounderCalculator(data).calculate()
        self.assertIsNone(result["comfort_runway_months"])


# ---------------------------------------------------------------------------
# 6. StandardFounderCalculator — founder_salary_start_year
# ---------------------------------------------------------------------------

class StandardFounderSalaryStartTests(TestCase):

    def _make_data(self, salary=50_000, start_months=0, **asset_overrides):
        assets = {
            "liquid": 2_000_000,
            "semi_liquid": 1_000_000,
            "growth": 3_000_000,
            "property": 0,
        }
        assets.update(asset_overrides)
        return {
            "family": {"monthly_expenses": 80_000, "one_time_expenses": 0},
            "assets": assets,
            "income": {"passive_monthly": 0},
            "profile": {"emergency_fund_months": 6},
            "scenario": {
                "venture_bootstrapped": False,
                "bootstrap_capital": 0,
                "parttime_monthly_income": salary,
                "founder_salary_start_month": start_months,
            },
            "rates": {},
        }

    def test_salary_from_day_one(self):
        data = self._make_data(salary=50_000, start_months=0)
        calc = StandardFounderCalculator(data)
        calc.calculate()
        # Year 0 income should include the salary
        self.assertGreater(calc.income_values[0], 0)

    def test_salary_delayed_by_one_year(self):
        data = self._make_data(salary=50_000, start_months=12)
        calc = StandardFounderCalculator(data)
        calc.calculate()
        # Year 0 income = 0 (before salary starts)
        self.assertAlmostEqual(calc.income_values[0], 0, delta=1)
        # Year 1 income > 0 (salary has started)
        self.assertGreater(calc.income_values[1], 0)

    def test_zero_salary_never_appears(self):
        data = self._make_data(salary=0, start_months=0)
        calc = StandardFounderCalculator(data)
        calc.calculate()
        for val in calc.income_values:
            self.assertAlmostEqual(val, 0, delta=1)

    def test_scenario_results_include_start_year(self):
        data = self._make_data(salary=50_000, start_months=24)
        result = StandardFounderCalculator(data).calculate()
        self.assertIn("founder_salary_start_year", result)
        self.assertEqual(result["founder_salary_start_year"], 2)


# ---------------------------------------------------------------------------
# 7. kids_independence_year uses user-supplied age
# ---------------------------------------------------------------------------

class KidsIndependenceYearTests(TestCase):

    def _make_data_with_kids(self, kids_avg_age, independence_age=None):
        data = _base_standard_data()
        data["family"].update({
            "kids_count": 1,
            "kids_average_age": kids_avg_age,
        })
        if independence_age is not None:
            data["family"]["kids_independence_age"] = independence_age
        return data

    def test_default_independence_age_is_24(self):
        calc = _ConcreteStandardCalc(self._make_data_with_kids(10))
        calc._load_rates()
        calc._read_common_inputs()
        # Expected: 24 - 10 = 14 years
        self.assertEqual(calc.kids_independence_year, 14)

    def test_custom_independence_age_used(self):
        calc = _ConcreteStandardCalc(self._make_data_with_kids(10, independence_age=22))
        calc._load_rates()
        calc._read_common_inputs()
        # Expected: 22 - 10 = 12 years
        self.assertEqual(calc.kids_independence_year, 12)

    def test_independence_age_older_than_default(self):
        calc = _ConcreteStandardCalc(self._make_data_with_kids(5, independence_age=28))
        calc._load_rates()
        calc._read_common_inputs()
        self.assertEqual(calc.kids_independence_year, 23)

    def test_no_kids_gives_none(self):
        data = _base_standard_data()
        data["family"]["kids_count"] = 0
        calc = _ConcreteStandardCalc(data)
        calc._load_rates()
        calc._read_common_inputs()
        self.assertIsNone(calc.kids_independence_year)

    def test_already_independent_clamps_to_zero(self):
        # Kid age 26, independence 24 → already past → clamp to 0
        calc = _ConcreteStandardCalc(self._make_data_with_kids(26, independence_age=24))
        calc._load_rates()
        calc._read_common_inputs()
        self.assertEqual(calc.kids_independence_year, 0)


# ---------------------------------------------------------------------------
# 8. calculate_tier view injects rate prefs
# ---------------------------------------------------------------------------

class CalculateTierInjectsRatesTests(TestCase):

    def setUp(self):
        self.user = make_user("tieruser")
        self.client = Client()
        self.client.force_login(self.user)
        FamilyProfile.objects.create(user=self.user, current_tier=1)
        ScenarioProfile.objects.create(user=self.user, scenario_type="FOUNDER")

    def test_rate_prefs_created_on_calculate(self):
        """Calling calculate_tier must create UserRatePreferences if absent."""
        payload = {
            "data": {
                "family": {
                    "monthly_expenses": 50000,
                    "monthly_needs": 30000,
                    "monthly_wants": 20000,
                    "one_time_expenses": 0,
                },
                "assets": {"living_total": 2_000_000, "security_total": 1_000_000},
                "income": {"passive_monthly": 0},
                "profile": {"emergency_fund_months": 6},
                "scenario": {"venture_bootstrapped": False, "bootstrap_capital": 0},
            }
        }
        resp = self.client.post(
            "/api/scenarios/calculate/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(UserRatePreferences.objects.filter(user=self.user).exists())

    def test_custom_rate_flows_into_calculation(self):
        """If user has a custom growth rate, calculation should use it."""
        # Set a custom rate before calculating
        UserRatePreferences.objects.create(user=self.user, growth_return_pct=15.0)
        payload = {
            "data": {
                "family": {
                    "monthly_expenses": 50000,
                    "monthly_needs": 30000,
                    "monthly_wants": 20000,
                    "one_time_expenses": 0,
                },
                "assets": {"living_total": 2_000_000, "security_total": 1_000_000},
                "income": {"passive_monthly": 0},
                "profile": {"emergency_fund_months": 6},
                "scenario": {"venture_bootstrapped": False, "bootstrap_capital": 0},
            }
        }
        resp = self.client.post(
            "/api/scenarios/calculate/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        # The response itself doesn't echo rates, but no exception should occur
        result = resp.json()
        self.assertIn("results", result)
