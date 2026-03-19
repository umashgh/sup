"""
Standard tier calculator for Termination / Job Loss scenario.
20-year projection: job search phase → income restart.
"""

from typing import Dict
from ..base import StandardBaseCalculator


class StandardTerminationCalculator(StandardBaseCalculator):
    """
    Termination scenario: severance added to available cash,
    Phase 1 (job search) → Phase 2 (income restart).
    """

    RESTART_INCOME_GROWTH = 0.08

    def _read_scenario_inputs(self):
        self.severance_lumpsum = float(self.get_field_value('scenario.severance_lumpsum', 0))
        self.income_restart_month = int(self.get_field_value('scenario.income_restart_month', 0))
        self.restart_monthly_income = float(self.get_field_value('scenario.restart_monthly_income', 0))
        self.restart_year = self.income_restart_month / 12.0

        self.survived_to_restart = True
        self.phase2_start_year = None

    def _compute_available_cash(self):
        """Add severance to available cash."""
        upfront_one_time = 0 if self.one_time_by_year else self.one_time_expenses

        # Display / runway: total assets + severance − emergency − one-time
        self.available_cash = max(
            0,
            self.total_assets_initial + self.severance_lumpsum
            - self.emergency_lock - upfront_one_time
        )

        # Projection buckets: deduct lock from liquid first, then semi_liquid
        to_deduct = self.emergency_lock + upfront_one_time
        liquid_deducted = min(self.liquid_savings, to_deduct)
        self.proj_liquid = self.liquid_savings - liquid_deducted + self.severance_lumpsum
        semi_deducted = min(self.semi_liquid, to_deduct - liquid_deducted)
        self.proj_semi = self.semi_liquid - semi_deducted

    def _init_projection_state(self, st: dict):
        st['restart_income'] = 0.0  # Activates at restart_year

    def _compute_year_income(self, year: int, st: dict) -> float:
        in_phase1 = year < self.restart_year
        if not in_phase1:
            return st['restart_income']
        return 0.0

    def _post_snapshot_hook(self, year, st, total_assets, total_income, total_expenses):
        in_phase1 = year < self.restart_year
        if not in_phase1 and self.phase2_start_year is None:
            self.phase2_start_year = year
            st['restart_income'] = self.restart_monthly_income * 12
        if in_phase1 and total_assets <= 0:
            self.survived_to_restart = False

    def _inflate_scenario(self, year: int, st: dict):
        if year >= self.restart_year and st['restart_income'] > 0:
            st['restart_income'] *= (1 + self.RESTART_INCOME_GROWTH)

    def _get_scenario_results(self) -> Dict:
        sustainable = self.final_corpus > (self.annual_survival * 5)
        return {
            'survived_to_restart': self.survived_to_restart,
            'sustainable': sustainable,
            'restart_year': round(self.restart_year, 1),
            'income_restart_month': self.income_restart_month,
            'phase2_start_year': self.phase2_start_year,
            'severance_lumpsum': round(self.severance_lumpsum, 2),
            'restart_monthly_income': round(self.restart_monthly_income, 2),
            'scenario_type': 'TERMINATION',
            'tier': 'STANDARD',
        }
