"""
Standard tier calculator for Founder scenario.
20-year projection with venture costs and founder salary draw.
"""

from typing import Dict
from ..base import StandardBaseCalculator


class StandardFounderCalculator(StandardBaseCalculator):
    """
    Founder scenario: bootstrap capital deducted from available cash,
    founder salary draw treated as earned income throughout.
    """

    def _read_scenario_inputs(self):
        self.venture_bootstrapped = self.get_field_value('scenario.venture_bootstrapped', False)
        self.bootstrap_capital = (
            float(self.get_field_value('scenario.bootstrap_capital', 0))
            if self.venture_bootstrapped else 0
        )
        self.founder_salary = float(self.get_field_value('scenario.parttime_monthly_income', 0))
        # Months from now before the salary begins (0 = from day one)
        self.founder_salary_start_year = (
            int(self.get_field_value('scenario.founder_salary_start_month', 0) or 0) // 12
        )

    def _compute_available_cash(self):
        """Deduct bootstrap capital in addition to the standard deductions."""
        upfront_one_time = 0 if self.one_time_by_year else self.one_time_expenses

        # Display / runway: total assets − emergency − bootstrap − one-time
        self.available_cash = max(
            0,
            self.total_assets_initial - self.emergency_lock
            - self.bootstrap_capital - upfront_one_time
        )

        # Projection buckets: deduct lock + bootstrap from liquid first, then semi
        to_deduct = self.emergency_lock + self.bootstrap_capital + upfront_one_time
        liquid_deducted = min(self.liquid_savings, to_deduct)
        self.proj_liquid = self.liquid_savings - liquid_deducted
        semi_deducted = min(self.semi_liquid, to_deduct - liquid_deducted)
        self.proj_semi = self.semi_liquid - semi_deducted

    def _get_monthly_earned_income(self) -> float:
        return self.founder_salary

    def _init_projection_state(self, st: dict):
        st['founder_salary'] = self.founder_salary * 12

    def _compute_year_income(self, year: int, st: dict) -> float:
        if year < self.founder_salary_start_year:
            return 0.0
        return st['founder_salary']

    def _inflate_scenario(self, year: int, st: dict):
        st['founder_salary'] *= (1 + self.PASSIVE_GROWTH)

    def _get_scenario_results(self) -> Dict:
        return {
            'bootstrap_capital': round(self.bootstrap_capital, 2),
            'founder_salary_monthly': round(self.founder_salary, 2),
            'founder_salary_start_year': self.founder_salary_start_year,
            'scenario_type': 'FOUNDER',
            'tier': 'STANDARD',
        }
