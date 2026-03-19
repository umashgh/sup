"""
Standard tier calculator for R2I (Return to India) scenario.
20-year projection with foreign pension and India work income.
"""

from typing import Dict
from ..base import StandardBaseCalculator


class StandardR2ICalculator(StandardBaseCalculator):
    """
    R2I scenario: foreign pension (starts at pension_start_age),
    India part-time/consulting work income throughout.
    """

    WORK_INCOME_GROWTH = 0.05
    PENSION_INFLATION = 0.04

    def _read_scenario_inputs(self):
        self.pension_monthly = float(self.get_field_value('scenario.pension_monthly', 0))
        self.pension_start_age = int(self.get_field_value('scenario.pension_start_age', 65))
        self.current_age = int(self.get_field_value('scenario.current_age', 35))
        self.india_work_monthly = float(self.get_field_value('scenario.parttime_monthly_income', 0))

        self.pension_start_year = self.pension_start_age - self.current_age

    def _get_monthly_earned_income(self) -> float:
        return self.india_work_monthly

    def _init_projection_state(self, st: dict):
        st['pension'] = self.pension_monthly * 12 if self.pension_monthly else 0
        st['india_work'] = self.india_work_monthly * 12

    def _compute_year_income(self, year: int, st: dict) -> float:
        pension = st['pension'] if year >= self.pension_start_year else 0
        return pension + st['india_work']

    def _post_snapshot_hook(self, year, st, total_assets, total_income, total_expenses):
        pass  # could track depletion; handled in _get_scenario_results

    def _inflate_scenario(self, year: int, st: dict):
        st['india_work'] *= (1 + self.WORK_INCOME_GROWTH)
        if year >= self.pension_start_year:
            st['pension'] *= (1 + self.PENSION_INFLATION)

    def _get_scenario_results(self) -> Dict:
        # Depletion year
        depletion_year = None
        for i, val in enumerate(self.assets_values):
            if val <= 0:
                depletion_year = i
                break

        current_corpus = self.liquid_savings + self.semi_liquid + self.growth_assets
        required_corpus = self.monthly_expenses * 12 * 25
        sustainable = self.final_corpus > (self.monthly_expenses * 12 * 5)

        return {
            'sustainable': sustainable,
            'depletion_year': depletion_year,
            'required_corpus': round(required_corpus, 2),
            'current_corpus': round(current_corpus, 2),
            'corpus_gap': round(max(0, required_corpus - current_corpus), 2),
            'india_work_income': round(self.india_work_monthly, 2),
            'pension_monthly': round(self.pension_monthly, 2),
            'pension_start_age': self.pension_start_age,
            'scenario_type': 'R2I',
            'tier': 'STANDARD',
        }
