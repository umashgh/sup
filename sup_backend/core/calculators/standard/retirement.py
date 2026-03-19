"""
Standard tier calculator for Retirement scenario.
20-year projection with pension and gratuity injection.
"""

from typing import Dict, List
from ..base import StandardBaseCalculator


class StandardRetirementCalculator(StandardBaseCalculator):
    """
    Retirement scenario: gratuity injected at retirement year,
    pension income begins at pension_start_age.
    """

    def _read_scenario_inputs(self):
        self.current_age = int(self.get_field_value('scenario.current_age', 30))
        self.retirement_age = int(self.get_field_value('scenario.retirement_age', 60))
        self.life_expectancy = int(self.get_field_value('scenario.life_expectancy', 85))

        self.pension_monthly = float(self.get_field_value('scenario.pension_monthly', 0))
        self.pension_start_age = int(self.get_field_value('scenario.pension_start_age', self.retirement_age))
        self.gratuity_lumpsum = float(self.get_field_value('scenario.gratuity_lumpsum', 0))

        self.years_to_retirement = max(0, self.retirement_age - self.current_age)
        self.retirement_duration = max(0, self.life_expectancy - self.retirement_age)
        self.pension_start_year = self.pension_start_age - self.current_age

        # Monthly savings needed to close gap
        current_corpus = self.liquid_savings + self.semi_liquid + self.growth_assets
        required_corpus = self.monthly_survival * 12 * 25
        corpus_gap = max(0, required_corpus - current_corpus)
        monthly_savings_rate = 0.10 / 12
        n_months = self.years_to_retirement * 12
        if n_months > 0 and corpus_gap > 0:
            fv_current = current_corpus * ((1 + monthly_savings_rate) ** n_months)
            remaining_gap = max(0, required_corpus - fv_current)
            if remaining_gap > 0 and monthly_savings_rate > 0:
                self.monthly_savings_needed = (
                    remaining_gap * monthly_savings_rate /
                    (((1 + monthly_savings_rate) ** n_months) - 1)
                )
            else:
                self.monthly_savings_needed = 0.0
        else:
            self.monthly_savings_needed = 0.0

    def _init_projection_state(self, st: dict):
        st['pension'] = self.pension_monthly * 12 if self.pension_monthly else 0

    def _pre_year_hook(self, year: int, st: dict):
        # Inject gratuity at retirement year
        if year == self.years_to_retirement and self.gratuity_lumpsum > 0:
            st['liquid'] += self.gratuity_lumpsum

    def _compute_year_income(self, year: int, st: dict) -> float:
        # Pension kicks in at pension_start_year
        if year >= self.pension_start_year:
            return st['pension']
        return 0.0

    def _inflate_scenario(self, year: int, st: dict):
        if year >= self.pension_start_year:
            st['pension'] *= (1 + 0.04)  # pension inflation

    def _get_scenario_results(self) -> Dict:
        # Depletion year
        depletion_year = None
        for i, val in enumerate(self.assets_values):
            if val <= 0:
                depletion_year = i
                break

        current_corpus = self.liquid_savings + self.semi_liquid + self.growth_assets
        required_corpus = self.annual_survival * 25
        sustainable = self.final_corpus > (self.monthly_expenses * 12 * 5)

        return {
            'years_to_retirement': self.years_to_retirement,
            'retirement_duration': self.retirement_duration,
            'sustainable': sustainable,
            'depletion_year': depletion_year,
            'required_corpus': round(required_corpus, 2),
            'current_corpus': round(current_corpus, 2),
            'corpus_gap': round(max(0, required_corpus - current_corpus), 2),
            'monthly_savings_needed': round(self.monthly_savings_needed, 2),
            'scenario_type': 'RETIREMENT',
            'tier': 'STANDARD',
        }

    def get_required_fields(self) -> List[str]:
        base = super().get_required_fields()
        return base + [
            'scenario.current_age',
            'scenario.retirement_age',
            'scenario.life_expectancy',
        ]
