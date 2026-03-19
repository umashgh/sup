"""
Standard tier calculator for Half-FIRE scenario.
20-year projection: part-time work → full financial independence.
"""

from typing import Dict
from ..base import StandardBaseCalculator


class StandardHalfFireCalculator(StandardBaseCalculator):
    """
    Half-FIRE scenario: part-time income in Phase 1 (up to full_fire_target),
    then fully stopped in Phase 2.
    """

    PARTTIME_GROWTH = 0.05

    def _read_scenario_inputs(self):
        self.parttime_monthly = float(self.get_field_value('scenario.parttime_monthly_income', 0))
        self.full_fire_target_month = int(self.get_field_value('scenario.full_fire_target_month', 60))
        self.full_fire_target_year = self.full_fire_target_month / 12.0

        self.phase2_start_year = None
        self.phase2_sustainable = True

    def _get_monthly_earned_income(self) -> float:
        return self.parttime_monthly

    def _init_projection_state(self, st: dict):
        st['parttime'] = self.parttime_monthly * 12

    def _compute_year_income(self, year: int, st: dict) -> float:
        # Phase 1: parttime active; Phase 2: stopped
        if year < self.full_fire_target_year:
            return st['parttime']
        return 0.0

    def _post_snapshot_hook(self, year, st, total_assets, total_income, total_expenses):
        in_phase1 = year < self.full_fire_target_year
        if not in_phase1 and self.phase2_start_year is None:
            self.phase2_start_year = year
        if not in_phase1 and total_assets <= 0:
            self.phase2_sustainable = False

    def _inflate_scenario(self, year: int, st: dict):
        if year < self.full_fire_target_year:
            st['parttime'] *= (1 + self.PARTTIME_GROWTH)

    def _get_scenario_results(self) -> Dict:
        return {
            'full_fire_target_year': round(self.full_fire_target_year, 1),
            'full_fire_target_month': self.full_fire_target_month,
            'phase2_start_year': self.phase2_start_year,
            'phase2_sustainable': self.phase2_sustainable,
            'parttime_monthly_income': round(self.parttime_monthly, 2),
            'scenario_type': 'HALF_FIRE',
            'tier': 'STANDARD',
        }
