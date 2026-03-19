"""
Quick tier calculator for Half-FIRE / Part-time scenario.
"""

from typing import Dict, List
from ..base import BaseCalculator


class QuickHalfFireCalculator(BaseCalculator):
    def calculate(self) -> Dict:
        """
        Perform quick Half-FIRE target calculation.
        """
        # Get user inputs
        monthly_expenses = float(self.get_field_value('family.monthly_expenses', 0))
        living_assets = float(self.get_field_value('assets.living_total', 0))
        security_assets = float(self.get_field_value('assets.security_total', 0))
        total_assets = living_assets + security_assets
        monthly_passive = float(self.get_field_value('income.passive_monthly', 0))
        emergency_fund_months = int(self.get_field_value('profile.emergency_fund_months', 6))
        
        # Scenario-specific inputs
        current_monthly_salary = float(self.get_field_value('scenario.current_monthly_salary', 0))
        parttime_monthly_income = float(self.get_field_value('scenario.parttime_monthly_income', 0))

        # Check for one-time expenses (Will be added in a later PR step)
        one_time_expenses = float(self.get_field_value('family.one_time_expenses', 0))

        # Use actual needs/wants from computed expense breakdown
        monthly_survival = float(self.get_field_value('family.monthly_needs', 0))
        monthly_lifestyle = float(self.get_field_value('family.monthly_wants', 0))
        # Fallback for old sessions without computed breakdown
        if monthly_survival == 0 and monthly_lifestyle == 0 and monthly_expenses > 0:
            monthly_survival = monthly_expenses * 0.6
            monthly_lifestyle = monthly_expenses * 0.4

        survival_burn = monthly_survival
        comfort_burn = monthly_expenses

        emergency_fund_lock = survival_burn * emergency_fund_months
        
        # Subtract emergency lock and one-time expenses
        available_cash = max(0, total_assets - emergency_fund_lock - one_time_expenses)

        # In half-fire, passive income AND part-time income cover the burn
        net_survival_burn = survival_burn - monthly_passive - parttime_monthly_income
        net_comfort_burn = comfort_burn - monthly_passive - parttime_monthly_income

        if net_survival_burn > 0:
            austerity_runway_months = available_cash / net_survival_burn
        else:
            austerity_runway_months = float('inf')

        if net_comfort_burn > 0:
            comfort_runway_months = available_cash / net_comfort_burn
        else:
            comfort_runway_months = float('inf')

        annual_survival = monthly_survival * 12
        target_number = annual_survival * 25
        target_gap = max(0, target_number - total_assets)

        return {
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
            'parttime_monthly_income': round(parttime_monthly_income, 2),
            'austerity_runway_months': round(austerity_runway_months, 1) if austerity_runway_months != float('inf') else None,
            'comfort_runway_months': round(comfort_runway_months, 1) if comfort_runway_months != float('inf') else None,
            'target_number': round(target_number, 2),
            'target_gap': round(target_gap, 2),
            'scenario_type': 'HALF_FIRE',
            'tier': 'QUICK',
        }

    def get_required_fields(self) -> List[str]:
        return [
            'family.monthly_expenses',
            'assets.living_total',
            'assets.security_total',
            'profile.emergency_fund_months',
        ]
