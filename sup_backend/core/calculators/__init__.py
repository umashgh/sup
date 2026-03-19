"""
Calculator factory for multi-scenario financial calculations.
Maps (scenario_type, tier) combinations to calculator classes.
"""

from .base import BaseCalculator
from .quick.founder import QuickFounderCalculator
from .quick.retirement import QuickRetirementCalculator
from .quick.r2i import QuickR2ICalculator
from .quick.half_fire import QuickHalfFireCalculator
from .quick.termination import QuickTerminationCalculator

# Import standard tier calculators
from .standard.founder import StandardFounderCalculator
from .standard.retirement import StandardRetirementCalculator
from .standard.r2i import StandardR2ICalculator
from .standard.half_fire import StandardHalfFireCalculator
from .standard.termination import StandardTerminationCalculator


# Calculator registry: maps (scenario_type, tier) to calculator class
CALCULATOR_MAP = {
    # Quick tier
    ('FOUNDER', 'QUICK'): QuickFounderCalculator,
    ('RETIREMENT', 'QUICK'): QuickRetirementCalculator,
    ('R2I', 'QUICK'): QuickR2ICalculator,
    ('HALF_FIRE', 'QUICK'): QuickHalfFireCalculator,
    ('TERMINATION', 'QUICK'): QuickTerminationCalculator,

    # Standard tier
    ('FOUNDER', 'STANDARD'): StandardFounderCalculator,
    ('RETIREMENT', 'STANDARD'): StandardRetirementCalculator,
    ('R2I', 'STANDARD'): StandardR2ICalculator,
    ('HALF_FIRE', 'STANDARD'): StandardHalfFireCalculator,
    ('TERMINATION', 'STANDARD'): StandardTerminationCalculator,
}


def get_calculator(scenario_type: str, tier: str, user_data: dict) -> BaseCalculator:
    """
    Factory function to get the appropriate calculator instance.

    Args:
        scenario_type: The scenario type (FOUNDER, RETIREMENT, etc.)
        tier: The calculation tier (QUICK, STANDARD, ADVANCED)
        user_data: User data dictionary

    Returns:
        Instantiated calculator object

    Raises:
        ValueError: If no calculator found for the given combination
    """
    key = (scenario_type, tier)
    calculator_class = CALCULATOR_MAP.get(key)

    if not calculator_class:
        raise ValueError(
            f"No calculator found for scenario='{scenario_type}' tier='{tier}'. "
            f"Available combinations: {list(CALCULATOR_MAP.keys())}"
        )

    return calculator_class(user_data)


__all__ = ['BaseCalculator', 'get_calculator', 'CALCULATOR_MAP']
