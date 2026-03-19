"""
Quick tier calculator for Retirement scenario.
Provides fast, simple calculations for retirement planning.
"""

from typing import Dict, List
from decimal import Decimal
from ..base import BaseCalculator


class QuickRetirementCalculator(BaseCalculator):
    """
    Quick retirement calculator.

    Calculates:
    - Years to retirement
    - Required corpus at retirement (using 4% SWR / 25x rule)
    - Current corpus
    - Corpus gap
    - Monthly savings needed to bridge the gap
    - Retirement duration (years in retirement)
    """

    def calculate(self) -> Dict:
        """
        Perform quick retirement calculation.

        Returns:
            Dictionary with retirement projections
        """
        # Get user inputs
        current_age = int(self.get_field_value('scenario.current_age', 30))
        retirement_age = int(self.get_field_value('scenario.retirement_age', 60))
        life_expectancy = int(self.get_field_value('scenario.life_expectancy', 85))
        emergency_fund_months = int(self.get_field_value('scenario.emergency_fund_months', 6))
        current_monthly_salary = float(self.get_field_value('scenario.current_monthly_salary', 0))

        monthly_expenses = float(self.get_field_value('family.monthly_expenses', 0))
        one_time_expenses = float(self.get_field_value('family.one_time_expenses', 0))

        living_assets = float(self.get_field_value('assets.living_total', 0))
        security_assets = float(self.get_field_value('assets.security_total', 0))
        monthly_passive = float(self.get_field_value('income.passive_monthly', 0))

        # Years to retirement
        years_to_retirement = max(0, retirement_age - current_age)

        # Use actual needs/wants from computed expense breakdown
        monthly_survival = float(self.get_field_value('family.monthly_needs', 0))
        monthly_lifestyle = float(self.get_field_value('family.monthly_wants', 0))
        # Fallback for old sessions without computed breakdown
        if monthly_survival == 0 and monthly_lifestyle == 0 and monthly_expenses > 0:
            monthly_survival = monthly_expenses * 0.6
            monthly_lifestyle = monthly_expenses * 0.4
        survival_burn = monthly_survival - monthly_passive
        comfort_burn = monthly_lifestyle

        # Required corpus at retirement (4% SWR = 25x annual expenses)
        annual_expenses = monthly_expenses * 12
        required_corpus = annual_expenses * 25

        # Current corpus (all assets combined)
        current_corpus = living_assets + security_assets
        total_assets = current_corpus # Renamed for clarity in new calculations

        # Emergency fund lock
        emergency_fund_lock = monthly_survival * emergency_fund_months

        # Available cash starts from total assets minus emergency lock and one-time expenses
        available_cash = max(0, total_assets - emergency_fund_lock - one_time_expenses)

        # Corpus gap
        corpus_gap = max(0, required_corpus - current_corpus)

        # Monthly savings needed
        months_remaining = years_to_retirement * 12
        if months_remaining > 0 and corpus_gap > 0:
            monthly_savings_needed = corpus_gap / months_remaining
        else:
            monthly_savings_needed = 0

        # Retirement duration
        retirement_duration_years = max(0, life_expectancy - retirement_age)

        # Passive income adequacy
        passive_income_annual = monthly_passive * 12
        passive_income_pct = (passive_income_annual / annual_expenses * 100) if annual_expenses > 0 else 0

        # Runway calculations (how long assets last if retired today)
        net_survival_burn = monthly_survival - monthly_passive
        net_comfort_burn = monthly_expenses - monthly_passive

        if net_survival_burn > 0:
            austerity_runway_months = available_cash / net_survival_burn
        else:
            austerity_runway_months = float('inf')

        if net_comfort_burn > 0:
            comfort_runway_months = available_cash / net_comfort_burn
        else:
            comfort_runway_months = float('inf')

        # Can retire today?
        can_retire_now = (
            current_corpus >= required_corpus or
            passive_income_annual >= annual_expenses
        )

        return {
            'years_to_retirement': years_to_retirement,
            'required_corpus': round(required_corpus, 2),
            'current_corpus': round(current_corpus, 2),
            'corpus_gap': round(corpus_gap, 2),
            'monthly_savings_needed': round(monthly_savings_needed, 2),
            'retirement_duration_years': retirement_duration_years,
            'annual_expenses': round(annual_expenses, 2),
            'passive_income_annual': round(passive_income_annual, 2),
            'passive_income_pct': round(passive_income_pct, 1),
            'can_retire_now': can_retire_now,
            'scenario_type': 'RETIREMENT',
            'tier': 'QUICK',
            'monthly_survival': round(monthly_survival, 2),
            'monthly_lifestyle': round(monthly_lifestyle, 2),
            'monthly_expenses': round(monthly_expenses, 2),
            'survival_burn': round(survival_burn, 2),
            'comfort_burn': round(comfort_burn, 2),
            'emergency_fund_lock': round(emergency_fund_lock, 2),
            'one_time_expenses': round(one_time_expenses, 2),
            'available_cash': round(available_cash, 2),
            'total_assets': round(total_assets, 2),
            'living_assets': round(living_assets, 2),
            'security_assets': round(security_assets, 2),
            'monthly_passive': round(monthly_passive, 2),
            'austerity_runway_months': round(austerity_runway_months, 1) if austerity_runway_months != float('inf') else None,
            'comfort_runway_months': round(comfort_runway_months, 1) if comfort_runway_months != float('inf') else None,
            'target_number': round(required_corpus, 2),
            'target_gap': round(corpus_gap, 2),
        }

    def get_required_fields(self) -> List[str]:
        """
        Returns list of required fields for this calculation.
        """
        return [
            'scenario.current_age',
            'scenario.retirement_age',
            'scenario.life_expectancy',
            'family.monthly_expenses',
            'assets.living_total',
            'assets.security_total',
        ]
