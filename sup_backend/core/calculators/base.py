"""
Base calculator interface for all scenario calculations.
Each scenario/tier combination has its own calculator implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import json


class BaseCalculator(ABC):
    """
    Abstract base class for all calculators.
    Each calculator is responsible for one scenario at one tier level.
    """

    def __init__(self, user_data: Dict):
        """
        Initialize calculator with user data.

        Args:
            user_data: Dictionary containing all user input data
                Format: {
                    'scenario': {...},  # ScenarioProfile fields
                    'family': {...},    # FamilyProfile fields
                    'assets': {...},    # Asset data
                    'income': {...},    # Income data
                    'expenses': {...},  # Expense data
                }
        """
        self.user_data = user_data

    @abstractmethod
    def calculate(self) -> Dict:
        """
        Perform the calculation and return results.

        Returns:
            Dictionary containing calculation results.
            Format varies by scenario and tier.
        """
        pass

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        Returns list of required data fields for this calculation.

        Returns:
            List of field paths (e.g., ['scenario.current_age', 'family.monthly_expenses'])
        """
        pass

    def validate_inputs(self) -> tuple[bool, List[str]]:
        """
        Validates that all required fields are present in user_data.

        Returns:
            Tuple of (is_valid, list_of_missing_fields)
        """
        required = self.get_required_fields()
        missing = []

        for field_path in required:
            parts = field_path.split('.')
            data = self.user_data

            try:
                for part in parts:
                    data = data[part]
                if data is None:
                    missing.append(field_path)
            except (KeyError, TypeError):
                missing.append(field_path)

        return len(missing) == 0, missing

    def get_field_value(self, field_path: str, default=None):
        """
        Helper to safely get nested field values from user_data.

        Args:
            field_path: Dot-separated path (e.g., 'scenario.current_age')
            default: Default value if field not found

        Returns:
            Field value or default
        """
        parts = field_path.split('.')
        data = self.user_data

        try:
            for part in parts:
                data = data[part]
            return data if data is not None else default
        except (KeyError, TypeError):
            return default


class StandardBaseCalculator(BaseCalculator):
    """
    Shared base for all Standard-tier (20-year projection) calculators.

    Template-method pattern: `calculate()` drives the pipeline;
    subclasses override hooks to inject scenario-specific behaviour.

    Pipeline:
        1. _read_common_inputs()       — shared fields
        2. _read_scenario_inputs()     — hook
        3. _compute_available_cash()   — overridable
        4. _compute_summary_metrics()  — runway / target gap
        5. _run_projection()           — 20-year loop
        6. _build_results()            — assemble return dict
    """

    # ── Asset return constants ──────────────────────────────────────
    LIQUID_RETURN = 0.06
    SEMI_LIQUID_RETURN = 0.08
    GROWTH_RETURN = 0.12
    PROPERTY_APPRECIATION = 0.05
    PROPERTY_RENTAL_YIELD = 0.03
    SWR_RATE = 0.04

    # ── Inflation constants ─────────────────────────────────────────
    NEEDS_INFLATION = 0.06
    WANTS_INFLATION = 0.07
    PASSIVE_GROWTH = 0.04

    # ── Budget split ────────────────────────────────────────────────
    NEEDS_PCT = 0.6
    WANTS_PCT = 0.4

    PROJECTION_YEARS = 21  # 0..20

    # ================================================================
    #  Main entry point  #flow: calculate comes
    # ================================================================
    def calculate(self) -> Dict:
        self._load_rates()
        self._read_common_inputs()
        self._read_scenario_inputs()
        self._compute_available_cash()
        self._compute_summary_metrics()
        self._run_projection()
        return self._build_results()

    # ================================================================
    #  Step 0 — load rate overrides from user_data['rates']
    # ================================================================
    def _load_rates(self):
        r = self.user_data.get('rates', {})
        self.LIQUID_RETURN          = r.get('liquid_return',          self.LIQUID_RETURN)
        self.SEMI_LIQUID_RETURN     = r.get('semi_liquid_return',     self.SEMI_LIQUID_RETURN)
        self.GROWTH_RETURN          = r.get('growth_return',          self.GROWTH_RETURN)
        self.PROPERTY_APPRECIATION  = r.get('property_appreciation',  self.PROPERTY_APPRECIATION)
        self.PROPERTY_RENTAL_YIELD  = r.get('property_rental_yield',  self.PROPERTY_RENTAL_YIELD)
        self.NEEDS_INFLATION        = r.get('needs_inflation',        self.NEEDS_INFLATION)
        self.WANTS_INFLATION        = r.get('wants_inflation',        self.WANTS_INFLATION)
        self.PASSIVE_GROWTH         = r.get('passive_growth',         self.PASSIVE_GROWTH)
        self.SWR_RATE               = r.get('swr_rate',               self.SWR_RATE)

    # ================================================================
    #  Step 1 — read common inputs
    # ================================================================
    def _read_common_inputs(self):
        self.monthly_expenses = float(self.get_field_value('family.monthly_expenses', 0))
        self.liquid_savings = float(self.get_field_value('assets.liquid', 0))
        self.semi_liquid = float(self.get_field_value('assets.semi_liquid', 0))
        self.growth_assets = float(self.get_field_value('assets.growth', 0))
        self.property_value = float(self.get_field_value('assets.property', 0))

        self.monthly_passive = float(self.get_field_value('income.passive_monthly', 0))
        self.emergency_fund_months = int(self.get_field_value('profile.emergency_fund_months', 6))

        self.one_time_expenses = float(self.get_field_value('family.one_time_expenses', 0))

        # One-time expenses by year (Issue #3) — may be None / empty
        raw_by_year = self.get_field_value('family.one_time_by_year', None)
        self.one_time_by_year: Dict[int, float] = {}
        if raw_by_year and isinstance(raw_by_year, (dict, str)):
            if isinstance(raw_by_year, str):
                try:
                    raw_by_year = json.loads(raw_by_year)
                except (json.JSONDecodeError, TypeError):
                    raw_by_year = {}
            for k, v in raw_by_year.items():
                self.one_time_by_year[int(k)] = float(v)

        # Future assets by year (Issue #2) — may be None / empty
        raw_future = self.get_field_value('family.future_assets_by_year', None)
        self.future_assets_by_year: Dict[int, float] = {}
        if raw_future and isinstance(raw_future, (dict, str)):
            if isinstance(raw_future, str):
                try:
                    raw_future = json.loads(raw_future)
                except (json.JSONDecodeError, TypeError):
                    raw_future = {}
            for k, v in raw_future.items():
                self.future_assets_by_year[int(k)] = float(v)

        # Kids — read individual ages (family.kid_1_age, kid_2_age, …) when available,
        # fall back to the legacy single-average fields for old sessions.
        self.kids_count = int(self.get_field_value('family.kids_count', 0) or 0)
        self.kids_independence_year = None  # legacy single-trigger (unused when events set)
        self.kids_independence_events: list = []  # [(year_offset, count)] per child

        if self.kids_count > 0:
            has_individual = self.get_field_value('family.kid_1_age') is not None
            if has_individual:
                for idx in range(1, self.kids_count + 1):
                    age = int(self.get_field_value(f'family.kid_{idx}_age', 10) or 10)
                    indep_age = int(self.get_field_value(f'family.kid_{idx}_indep_age', 24) or 24)
                    year_offset = max(0, indep_age - age)
                    self.kids_independence_events.append(year_offset)
            else:
                # Legacy: single average age + independence age
                avg_age = int(self.get_field_value('family.kids_average_age', 10) or 10)
                indep_age = int(self.get_field_value('family.kids_independence_age', 24) or 24)
                year_offset = max(0, indep_age - avg_age)
                for _ in range(self.kids_count):
                    self.kids_independence_events.append(year_offset)

        # Derived annual values
        self.monthly_survival = self.monthly_expenses * self.NEEDS_PCT
        self.monthly_lifestyle = self.monthly_expenses * self.WANTS_PCT
        self.annual_survival = self.monthly_survival * 12
        self.annual_lifestyle = self.monthly_lifestyle * 12
        self.annual_passive = self.monthly_passive * 12

        # Emergency fund lock
        self.emergency_lock = self.monthly_survival * self.emergency_fund_months

        # Total initial assets
        self.total_assets_initial = (
            self.liquid_savings + self.semi_liquid +
            self.growth_assets + self.property_value
        )
        self.accessible_assets = self.liquid_savings + self.semi_liquid

    # ================================================================
    #  Step 2 — scenario-specific inputs (hook)
    # ================================================================
    def _read_scenario_inputs(self):
        """Override in subclass to read scenario-specific fields."""
        pass

    # ================================================================
    #  Step 3 — available cash
    # ================================================================
    def _compute_available_cash(self):
        """
        available_cash (for display & runway) = total_assets - emergency_lock - all_one_time.
        This matches the results template breakdown: total − emergency − one_time = available.

        For the 20-year projection, proj_liquid / proj_semi only deduct year-0
        one-time expenses from the starting state; future-year ones are handled
        in the projection loop to avoid double-counting.
        """
        # Display / runway: always deduct ALL one-time expenses so the template
        # breakdown (total − emergency − one_time = available) is consistent.
        self.available_cash = max(
            0,
            self.total_assets_initial - self.emergency_lock - self.one_time_expenses
        )

        # Projection starting state: only deduct year-0 one-time expenses
        # (future years are handled in _run_projection via one_time_by_year).
        if self.one_time_by_year:
            proj_one_time = self.one_time_by_year.get(0, 0.0)
        else:
            proj_one_time = self.one_time_expenses

        to_deduct = self.emergency_lock + proj_one_time
        liquid_deducted = min(self.liquid_savings, to_deduct)
        self.proj_liquid = self.liquid_savings - liquid_deducted
        semi_deducted = min(self.semi_liquid, to_deduct - liquid_deducted)
        self.proj_semi = self.semi_liquid - semi_deducted

    # ================================================================
    #  Step 4 — summary metrics (runway, target, gap)
    # ================================================================
    def _compute_summary_metrics(self):
        earned = self._get_monthly_earned_income()
        self.net_comfort_burn = max(0, self.monthly_expenses - self.monthly_passive - earned)
        self.net_survival_burn = max(0, self.monthly_survival - self.monthly_passive - earned)

        self.comfort_runway_months = (
            round(self.available_cash / self.net_comfort_burn, 1)
            if self.net_comfort_burn > 0 else None
        )
        self.austerity_runway_months = (
            round(self.available_cash / self.net_survival_burn, 1)
            if self.net_survival_burn > 0 else None
        )
        self.target_number = self.annual_survival * 25
        self.target_gap = max(0, self.target_number - self.total_assets_initial)

    # ================================================================
    #  Step 5 — 20-year projection loop
    # ================================================================
    def _run_projection(self):
        # Chart data lists
        self.years: List[str] = []
        self.assets_values: List[float] = []
        self.needs_values: List[float] = []
        self.wants_values: List[float] = []
        self.income_values: List[float] = []

        # Mutable state for the loop
        self.st = {
            'liquid': self.proj_liquid,
            'semi_liquid': self.proj_semi,
            'growth': self.growth_assets,
            'property': self.property_value,
            'needs': self.annual_survival,
            'wants': self.annual_lifestyle,
            'passive': self.annual_passive,
        }
        # Let subclass add extra state (e.g. founder_salary, parttime, pension)
        self._init_projection_state(self.st)

        self.free_up_year: Optional[int] = None
        self.corpus_fi_year: Optional[int] = None   # corpus × SWR covers expenses
        self.depletion_year: Optional[int] = None

        for year in range(self.PROJECTION_YEARS):
            self.years.append(f"Year {year}")

            # ── pre-year hook (gratuity injection, etc.) ──
            self._pre_year_hook(year, self.st)

            # ── future assets arriving this year (Issue #2) ──
            if year in self.future_assets_by_year:
                self.st['growth'] += self.future_assets_by_year[year]

            # ── one-time expenses this year (Issue #3) ──
            year_one_time = self.one_time_by_year.get(year, 0)

            # ── kids independence: staggered per child ──
            # Each kid adds ~10% to needs; reduce when that child becomes independent
            kids_becoming_independent = self.kids_independence_events.count(year)
            if kids_becoming_independent > 0:
                factor = 1.0 / (1.0 + 0.10 * kids_becoming_independent)
                self.st['needs'] *= factor

            # ── 1. snapshot ──
            total_assets = (
                self.st['liquid'] + self.st['semi_liquid'] +
                self.st['growth'] + self.st['property']
            )
            rental_income = self.st['property'] * self.PROPERTY_RENTAL_YIELD
            total_passive = self.st['passive'] + rental_income

            scenario_income = self._compute_year_income(year, self.st)
            total_income = total_passive + scenario_income
            total_expenses = self.st['needs'] + self.st['wants'] + year_one_time

            # free_up_year: passive + scenario income alone covers expenses
            # (no asset drawdown needed — true financial independence)
            if self.free_up_year is None and total_income >= total_expenses:
                self.free_up_year = year

            # corpus_fi_year: SWR from corpus alone covers inflation-adjusted expenses
            # (portfolio is self-sustaining even without passive income streams)
            swr_annual = total_assets * self.SWR_RATE
            if self.corpus_fi_year is None and swr_annual >= total_expenses:
                self.corpus_fi_year = year

            if self.depletion_year is None and total_assets <= 0:
                self.depletion_year = year

            self.assets_values.append(round(max(total_assets, 0), 2))
            self.needs_values.append(round(self.st['needs'], 2))
            self.wants_values.append(round(self.st['wants'], 2))
            self.income_values.append(round(total_income, 2))

            # ── post-snapshot hook (survival tracking, etc.) ──
            self._post_snapshot_hook(year, self.st, total_assets, total_income, total_expenses)

            # ── 2. deficit / surplus waterfall ──
            net = total_income - total_expenses
            self._handle_cashflow(self.st, net)

            # ── 3. grow assets ──
            self.st['liquid'] *= (1 + self.LIQUID_RETURN)
            self.st['semi_liquid'] *= (1 + self.SEMI_LIQUID_RETURN)
            self.st['growth'] *= (1 + self.GROWTH_RETURN)
            self.st['property'] *= (1 + self.PROPERTY_APPRECIATION)

            # ── 4. inflate expenses & income ──
            self.st['needs'] *= (1 + self.NEEDS_INFLATION)
            self.st['wants'] *= (1 + self.WANTS_INFLATION)
            self.st['passive'] *= (1 + self.PASSIVE_GROWTH)
            self._inflate_scenario(year, self.st)

        self.final_corpus = self.assets_values[-1]

    # ================================================================
    #  Step 6 — build results dict
    # ================================================================
    def _build_results(self) -> Dict:
        base = {
            'free_up_year': self.free_up_year,
            'corpus_fi_year': self.corpus_fi_year,
            'swr_rate': self.SWR_RATE,
            'depletion_year': self.depletion_year,
            'emergency_lock': round(self.emergency_lock, 2),
            'emergency_fund_lock': round(self.emergency_lock, 2),
            'one_time_expenses': round(self.one_time_expenses, 2),
            'available_cash': round(self.available_cash, 2),
            'total_assets': round(self.total_assets_initial, 2),
            'monthly_expenses': round(self.monthly_expenses, 2),
            'monthly_passive': round(self.monthly_passive, 2),
            'monthly_needs': round(self.monthly_survival, 2),
            'comfort_runway_months': self.comfort_runway_months,
            'austerity_runway_months': self.austerity_runway_months,
            'target_number': round(self.target_number, 2),
            'target_gap': round(self.target_gap, 2),
            'final_corpus': round(self.final_corpus, 2),
            'sustainable': self.final_corpus > (self.annual_survival * 5),
            'chart_data': {
                'years': self.years,
                'assets': self.assets_values,
                'needs': self.needs_values,
                'wants': self.wants_values,
                'incomes': self.income_values,
            },
        }
        # Merge scenario-specific results
        base.update(self._get_scenario_results())
        return base

    # ================================================================
    #  Deficit / surplus waterfall (shared)
    # ================================================================
    @staticmethod
    def _handle_cashflow(st: dict, net: float):
        if net < 0:
            deficit = abs(net)
            if st['liquid'] >= deficit:
                st['liquid'] -= deficit
            elif st['liquid'] + st['semi_liquid'] >= deficit:
                deficit -= st['liquid']
                st['liquid'] = 0
                st['semi_liquid'] -= deficit
            else:
                deficit -= (st['liquid'] + st['semi_liquid'])
                st['liquid'] = 0
                st['semi_liquid'] = 0
                st['growth'] = max(0, st['growth'] - deficit)
        else:
            st['growth'] += net

    # ================================================================
    #  Hooks for subclasses
    # ================================================================
    def _get_monthly_earned_income(self) -> float:
        """Monthly earned income for runway calc (founder salary, parttime, etc.)."""
        return 0.0

    def _init_projection_state(self, st: dict):
        """Add scenario-specific keys to the state dict before the loop."""
        pass

    def _pre_year_hook(self, year: int, st: dict):
        """Called at the start of each year (inject gratuity, etc.)."""
        pass

    def _compute_year_income(self, year: int, st: dict) -> float:
        """Return scenario-specific income for this year (beyond passive+SWR)."""
        return 0.0

    def _post_snapshot_hook(self, year: int, st: dict,
                            total_assets: float, total_income: float,
                            total_expenses: float):
        """Called after snapshot values are recorded (track survival, etc.)."""
        pass

    def _inflate_scenario(self, year: int, st: dict):
        """Inflate scenario-specific values (pension, parttime, etc.)."""
        pass

    def _get_scenario_results(self) -> Dict:
        """Return scenario-specific keys for the result dict."""
        return {}

    # ================================================================
    #  Required fields (common across all standard calculators)
    # ================================================================
    def get_required_fields(self) -> List[str]:
        return [
            'family.monthly_expenses',
            'assets.liquid',
            'assets.semi_liquid',
            'assets.growth',
            'assets.property',
            'profile.emergency_fund_months',
        ]
