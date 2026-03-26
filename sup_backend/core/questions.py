"""
Dynamic question configuration system for multi-scenario flow.
Questions are configured here and filtered by scenario, tier, and conditional logic.
"""

from typing import List, Dict, Callable, Optional


class Question:
    """
    Represents a single question in the dynamic flow.
    """
    def __init__(
        self,
        id: str,
        text: str,
        field_name: str,
        input_type: str,  # slider, amount_slider, year_slider, toggle, card_select, etc.
        tier: str,  # QUICK, STANDARD, ADVANCED
        scenarios: List[str],  # Which scenarios this applies to
        condition: Optional[Callable] = None,  # Function that determines if question should show
        options: Optional[List[Dict]] = None,  # For select/radio inputs
        validation: Optional[Dict] = None,
        slider_config: Optional[Dict] = None,  # For slider inputs
        help_text: Optional[str] = None,
        widget_category: str = 'info',  # info, expense, income, asset — for UI color coding
        text_by_scenario: Optional[Dict[str, str]] = None,  # scenario -> question text override
        help_by_scenario: Optional[Dict[str, str]] = None,  # scenario -> help text override
    ):
        self.id = id
        self.text = text
        self.field_name = field_name
        self.input_type = input_type
        self.tier = tier
        self.scenarios = scenarios
        self.condition = condition
        self.options = options or []
        self.validation = validation or {}
        self.slider_config = slider_config or {}
        self.help_text = help_text
        self.widget_category = widget_category
        self.text_by_scenario = text_by_scenario or {}
        self.help_by_scenario = help_by_scenario or {}

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'text': self.text,
            'field_name': self.field_name,
            'input_type': self.input_type,
            'tier': self.tier,
            'scenarios': self.scenarios,
            'options': self.options,
            'validation': self.validation,
            'slider_config': self.slider_config,
            'help_text': self.help_text,
            'widget_category': self.widget_category,
        }


# ============================================================================
# QUICK TIER QUESTIONS
# ============================================================================

QUESTIONS = [
    # Universal questions (all scenarios)
    Question(
        id="family_type",
        text="What's your family composition?",
        field_name="family_type",
        input_type="card_select",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        options=[
            {"value": "solo", "label": "Just me"},
            {"value": "partner", "label": "With partner"},
            {"value": "partner_kids", "label": "Partner + kids"},
            {"value": "joint", "label": "Joint family"},
        ]
    ),

    # ========================================================================
    # AGES — combined screen: your age + partner's age (conditional)
    # ========================================================================

    Question(
        id="ages",
        text="How old are you?",
        field_name="scenario.current_age",
        input_type="age_group",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        options=[
            {"field_name": "scenario.current_age", "label": "Your age", "min": 18, "max": 75, "default": 30},
            {"field_name": "family.spouse_age", "label": "Partner's age", "min": 18, "max": 75, "default": 30,
             "condition": "family_has_partner"},
        ],
    ),

    # Conditional: Dependent kids count and age
    Question(
        id="kids_count",
        text="How many dependent kids?",
        field_name="kids_count",
        input_type="slider",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        condition=lambda data: data.get("family_type") in ["partner_kids", "joint"],
        slider_config={
            "min": 0,
            "max": 5,
            "step": 1,
            "unit": "kids",
        },
        validation={"min": 0, "max": 5}
    ),

    Question(
        id="kids_average_age",
        text="How old is your kid?",
        field_name="family.kids_average_age",
        input_type="slider",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        condition=lambda data: (
            data.get("family_type") in ["partner_kids", "joint"]
            and int(data.get("kids_count", 0) or 0) > 0
        ),
        slider_config={
            "min": 0,
            "max": 30,
            "step": 1,
            "unit": "years",
            "default": 10,
        },
        validation={"min": 0, "max": 30},
        help_text="Used for estimating education and settling-down expenses."
    ),

    # Conditional: Dependent adults count (shows for all non-solo family types)
    Question(
        id="dependent_adults_count",
        text="How many dependent adults (parents, etc.)?",
        field_name="dependent_adults_count",
        input_type="slider",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        condition=lambda data: data.get("family_type") in ["partner", "partner_kids", "joint"],
        slider_config={
            "min": 0,
            "max": 4,
            "step": 1,
            "unit": "adults",
        },
        validation={"min": 0, "max": 4}
    ),

    # Household attributes — single screen with checkboxes
    Question(
        id="household_attributes",
        text="Tell us about your household",
        field_name="family.household_attrs",
        input_type="checkbox_group",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        options=[
            {"field_name": "family.has_vehicle", "label": "Own a vehicle", "emoji": "🚗", "default": True},
            {"field_name": "family.has_pet", "label": "Have a pet", "emoji": "🐾", "default": False},
            {"field_name": "family.rented_house", "label": "Live in a rented house", "emoji": "🏠", "default": True},
        ]
    ),

    # ========================================================================
    # FOUNDER-SPECIFIC QUESTIONS
    # ========================================================================

    Question(
        id="venture_bootstrapped",
        text="Are you bootstrapping this venture from savings?",
        field_name="scenario.venture_bootstrapped",
        input_type="toggle_with_amount",
        tier="QUICK",
        scenarios=["FOUNDER"],
        help_text="If yes, we'll account for the capital you're putting into the business.",
        options=[{
            "amount_field": "scenario.bootstrap_capital",
            "amount_label": "How much are you investing?",
            "min": 0, "max": 50000000, "step": 100000,
            "presets": [100000, 500000, 1000000, 5000000, 10000000],
        }]
    ),

    # ========================================================================
    # RETIREMENT-SPECIFIC QUESTIONS
    # ========================================================================

    Question(
        id="retirement_age",
        text="At what age do you plan to retire?",
        field_name="scenario.retirement_age",
        input_type="slider",
        tier="QUICK",
        scenarios=["RETIREMENT"],
        slider_config={
            "min": 35,
            "max": 75,
            "step": 1,
            "unit": "years",
        },
        validation={"min": 35, "max": 75}
    ),

    Question(
        id="life_expectancy",
        text="What's your expected lifespan?",
        field_name="scenario.life_expectancy",
        input_type="slider",
        tier="QUICK",
        scenarios=["RETIREMENT"],
        slider_config={
            "min": 65,
            "max": 100,
            "step": 1,
            "unit": "years",
            "default": 80,
        },
        validation={"min": 65, "max": 100},
        help_text="This helps us plan for the full retirement period."
    ),

    # ========================================================================
    # R2I-SPECIFIC QUESTIONS
    # ========================================================================

    Question(
        id="r2i_continue_working",
        text="Will you work in India?",
        field_name="scenario.parttime_monthly_income",
        input_type="toggle_with_amount",
        tier="QUICK",
        scenarios=["R2I"],
        help_text="Part-time, consulting, or a full-time role — any earned income reduces how much you draw from savings.",
        widget_category="income",
        options=[{
            "amount_field": "scenario.parttime_monthly_income",
            "amount_label": "Expected monthly income",
            "min": 0, "max": 500000, "step": 5000,
            "presets": [0, 25000, 50000, 100000, 200000],
        }]
    ),

    # ========================================================================
    # HALF_FIRE-SPECIFIC QUESTIONS
    # ========================================================================

    Question(
        id="parttime_monthly_income",
        text="Expected monthly income from part-time / freelance work?",
        field_name="scenario.parttime_monthly_income",
        input_type="amount_slider",
        tier="QUICK",
        scenarios=["HALF_FIRE"],
        slider_config={
            "min": 0,
            "max": 500000,
            "step": 5000,
            "unit": "₹/mo",
            "presets": [0, 25000, 50000, 100000, 200000],
        },
        validation={"min": 0},
        help_text="Income you expect from part-time, consulting, or freelance work."
    ),

    # ========================================================================
    # TERMINATION-SPECIFIC QUESTIONS
    # ========================================================================

    Question(
        id="severance_lumpsum",
        text="Expected severance / notice pay (one-time)?",
        field_name="scenario.severance_lumpsum",
        input_type="amount_slider",
        tier="QUICK",
        scenarios=["TERMINATION"],
        slider_config={
            "min": 0,
            "max": 50000000,
            "step": 100000,
            "unit": "₹",
            "presets": [0, 500000, 1000000, 2500000, 5000000],
        },
        validation={"min": 0},
        help_text="Include severance, notice period pay, and any other termination benefits."
    ),

    # ========================================================================
    # SHARED FINANCIAL QUESTIONS (all scenarios)
    # ========================================================================

    Question(
        id="expense_level",
        text="What's your spending style?",
        field_name="family.expense_level",
        input_type="card_select",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        options=[
            {"value": 1, "label": "Essential", "emoji": "🍞"},
            {"value": 2, "label": "Comfortable", "emoji": "☕"},
            {"value": 3, "label": "Premium", "emoji": "🥂"},
        ],
        widget_category="expense",
    ),

    Question(
        id="computed_expenses",
        text="Here's your estimated monthly expenses",
        field_name="family.monthly_expenses",
        input_type="expense_estimate",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        help_text="Based on your family and spending style. Tap to fine-tune.",
        widget_category="expense",
    ),

    Question(
        id="assets_for_living",
        text="Assets for living expenses: Cash, FDs, bonds, debt MFs, gold, etc.",
        help_text="Include all liquid and semi-liquid assets for the entire household that can be accessed within months",
        field_name="assets.living_total",
        input_type="amount_slider",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        slider_config={
            "min": 0,
            "max": 200000000,  # ₹20Cr
            "step": 100000,
            "unit": "₹",
            "presets": [1000000, 2500000, 5000000, 10000000, 25000000, 50000000],
        },
        validation={"min": 0},
        widget_category="asset",
        text_by_scenario={
            "R2I": "Money you're bringing back — for living",
            "TERMINATION": "Savings during job search",
            "HALF_FIRE": "Savings to bridge your transition",
            "FOUNDER": "Personal savings (outside venture)",
            "RETIREMENT": "Liquid savings at retirement",
        },
        help_by_scenario={
            "R2I": "Liquid savings you're repatriating to cover day-to-day living in India",
            "TERMINATION": "Liquid savings to sustain you while between jobs",
            "HALF_FIRE": "Liquid savings to draw on while scaling back to part-time",
            "FOUNDER": "Savings separate from your startup capital — to fund your lifestyle",
            "RETIREMENT": "Cash, FDs, and bonds you can draw from once retired",
        },
    ),

    Question(
        id="assets_for_security",
        text="Assets for future security: Equity, stocks, PF, NPS, real estate, etc.",
        help_text="Include all growth assets and property for the entire household",
        field_name="assets.security_total",
        input_type="amount_slider",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        slider_config={
            "min": 0,
            "max": 100000000,  # ₹10Cr
            "step": 100000,
            "unit": "₹",
            "presets": [1000000, 2500000, 5000000, 10000000, 25000000],
        },
        validation={"min": 0},
        widget_category="asset",
        text_by_scenario={
            "R2I": "Long-term wealth in India",
            "FOUNDER": "Security assets (personal, not venture)",
            "RETIREMENT": "Growth portfolio and property",
        },
        help_by_scenario={
            "R2I": "Growth assets and property you'll hold for future appreciation",
            "FOUNDER": "Property and growth investments separate from your startup",
            "RETIREMENT": "Equity, PF, NPS, and property that will compound over time",
        },
    ),

    Question(
        id="monthly_passive_income",
        text="What's your monthly passive income (rent, dividends, etc.)?",
        field_name="income.passive_monthly",
        input_type="amount_slider",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        slider_config={
            "min": 0,
            "max": 1000000,  # ₹10L per month
            "step": 5000,
            "unit": "₹/mo",
            "presets": [0, 10000, 25000, 50000, 100000],
        },
        validation={"min": 0},
        widget_category="income",
        text_by_scenario={
            "R2I": "Passive income in India",
            "TERMINATION": "Investment income between jobs",
            "RETIREMENT": "Passive income in retirement",
        },
        help_by_scenario={
            "R2I": "Rental income, dividends from Indian investments, or interest income",
            "TERMINATION": "Dividend or rental income reducing your burn rate while between roles",
            "RETIREMENT": "Rental, dividends, or other investment income each month",
        },
    ),

    Question(
        id="emergency_fund_months",
        text="How many months of emergency fund do you want locked?",
        field_name="profile.emergency_fund_months",
        input_type="slider",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        slider_config={
            "min": 3,
            "max": 24,
            "step": 1,
            "unit": "months",
            "default": 6,
        },
        validation={"min": 3, "max": 24},
        help_text="Kept aside as a safety net — not counted in your runway. Covers unexpected medical, repairs, or income gaps.",
        widget_category="asset",
    ),
    Question(
        id="one_time_expenses",
        text="Any big upcoming expenses?",
        field_name="family.one_time_expenses",
        input_type="one_time_itemized",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        help_text="Toggle items that apply. Amounts pre-filled from your spending level.",
        widget_category="expense",
        text_by_scenario={
            "R2I": "Relocation & setup costs",
        },
        help_by_scenario={
            "R2I": "Housing deposit, shipping, travel, or one-time R2I costs",
        },
    ),

    Question(
        id="future_assets",
        text="Do you expect any assets arriving later?",
        field_name="family.future_assets",
        input_type="future_asset_itemized",
        tier="QUICK",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        help_text="Inheritance, PF/EPF corpus, maturing investments, property sale, etc.",
        widget_category="asset",
    ),
]


# ============================================================================
# STANDARD TIER QUESTIONS (additional questions for deeper dive)
# ============================================================================

STANDARD_TIER_QUESTIONS = [
    Question(
        id="living_assets_split",
        text="Now let's split your Living Money between liquid and semi-liquid assets",
        help_text="You entered your total living assets earlier. Now divide it: how much in instantly accessible cash vs bonds/FDs that take a few days to liquidate?",
        field_name="assets.living_split_ratio",
        input_type="split_slider",
        tier="STANDARD",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        slider_config={
            "total_field": "assets.living_total",
            "field_1": "assets.liquid",
            "field_1_label": "Liquid Cash",
            "field_1_color": "var(--forest)",
            "field_1_growth": "6%",
            "field_2": "assets.semi_liquid",
            "field_2_label": "Bonds / Debt MFs",
            "field_2_color": "var(--mustard)",
            "field_2_growth": "8%",
            "default_percent": 60, # 60% liquid, 40% semi
        },
        widget_category="asset",
        text_by_scenario={
            "R2I": "Split your repatriated savings between liquid and semi-liquid",
        },
        help_by_scenario={
            "R2I": "Of the money you're bringing back, how much in immediately accessible cash vs bonds/FDs for stability?",
        },
    ),

    Question(
        id="security_assets_split",
        text="Now let's split your Security Money between growth assets and property",
        help_text="You entered your total security assets earlier. Now divide it: how much in equity/PF/stocks vs real estate/property?",
        field_name="assets.security_split_ratio",
        input_type="split_slider",
        tier="STANDARD",
        scenarios=["FOUNDER", "RETIREMENT", "R2I", "HALF_FIRE", "TERMINATION"],
        slider_config={
            "total_field": "assets.security_total",
            "field_1": "assets.growth",
            "field_1_label": "Equity, PF, NPS",
            "field_1_color": "var(--forest)",
            "field_1_growth": "12%",
            "field_2": "assets.property",
            "field_2_label": "Property",
            "field_2_color": "var(--ocean)",
            "field_2_growth": "5%",
            "default_percent": 70, # 70% growth, 30% property
        },
        widget_category="asset",
        text_by_scenario={
            "R2I": "Split your long-term wealth between growth assets and property",
        },
        help_by_scenario={
            "R2I": "Of your total long-term assets in India, how much is in equity/MFs vs property/real estate?",
        },
    ),

    # Retirement & R2I: Pension details
    Question(
        id="pension_monthly",
        text="Expected monthly pension amount?",
        field_name="scenario.pension_monthly",
        input_type="amount_slider",
        tier="STANDARD",
        scenarios=["RETIREMENT", "R2I"],
        slider_config={
            "min": 0,
            "max": 500000,
            "step": 5000,
            "unit": "₹/mo",
            "presets": [0, 10000, 25000, 50000, 100000],
        },
        validation={"min": 0},
        widget_category="income",
        text_by_scenario={
            "R2I": "Monthly pension from abroad",
        },
        help_by_scenario={
            "R2I": "Pension, 401k distributions, Social Security, or annuity income in INR",
        },
    ),

    Question(
        id="pension_start_age",
        text="At what age will pension start?",
        field_name="scenario.pension_start_age",
        input_type="slider",
        tier="STANDARD",
        scenarios=["RETIREMENT", "R2I"],
        condition=lambda data: float(data.get('scenario', {}).get('pension_monthly', 0) or 0) > 0,
        slider_config={
            "min": 50,
            "max": 75,
            "step": 1,
            "unit": "years",
        },
        validation={"min": 50, "max": 75},
        widget_category="income",
        text_by_scenario={
            "R2I": "When does it start (your age)?",
        },
    ),

    Question(
        id="gratuity_lumpsum",
        text="Expected gratuity amount (one-time)?",
        field_name="scenario.gratuity_lumpsum",
        input_type="amount_slider",
        tier="STANDARD",
        scenarios=["RETIREMENT"],
        slider_config={
            "min": 0,
            "max": 50000000,
            "step": 100000,
            "unit": "₹",
            "presets": [0, 500000, 1000000, 2500000, 5000000],
        },
        validation={"min": 0},
        widget_category="asset",
    ),

    # HALF_FIRE: Full FIRE target
    Question(
        id="halffire_fire_target",
        text="When do you aim to fully stop working?",
        field_name="scenario.full_fire_target_month",
        input_type="slider",
        tier="STANDARD",
        scenarios=["HALF_FIRE"],
        help_text="Your Full FIRE target — when part-time income is no longer needed. Used to model your transition curve.",
        widget_category="info",
        slider_config={
            "min": 12,
            "max": 240,
            "step": 6,
            "unit": "months",
            "default": 60,
        },
        validation={"min": 0, "max": 240},
    ),

    # TERMINATION: Restart timeline and income
    Question(
        id="termination_restart_timeline",
        text="When do you expect to start earning again?",
        field_name="scenario.income_restart_month",
        input_type="slider",
        tier="STANDARD",
        scenarios=["TERMINATION"],
        help_text="Approximate months until your next role. Keeps the projection realistic.",
        widget_category="info",
        slider_config={
            "min": 0,
            "max": 36,
            "step": 1,
            "unit": "months",
            "default": 6,
        },
        validation={"min": 0, "max": 36},
    ),

    Question(
        id="termination_restart_income",
        text="What income do you expect at your next role?",
        field_name="scenario.restart_monthly_income",
        input_type="amount_slider",
        tier="STANDARD",
        scenarios=["TERMINATION"],
        condition=lambda data: int((data.get('scenario') or {}).get('income_restart_month', 0) or 0) > 0,
        help_text="Estimated monthly salary after restart — models when the drawdown stops.",
        widget_category="income",
        slider_config={
            "min": 0,
            "max": 1000000,
            "step": 10000,
            "unit": "₹/mo",
            "presets": [50000, 100000, 200000, 300000, 500000],
        },
        validation={"min": 0},
    ),

    # FOUNDER: Salary draw from venture
    Question(
        id="founder_salary",
        text="Monthly salary you're drawing from your venture",
        field_name="scenario.parttime_monthly_income",
        input_type="amount_slider",
        tier="STANDARD",
        scenarios=["FOUNDER"],
        help_text="What you pay yourself from the company. Reduces personal burn — ₹0 is valid if you're not drawing yet.",
        widget_category="income",
        slider_config={
            "min": 0,
            "max": 500000,
            "step": 5000,
            "unit": "₹/mo",
            "presets": [0, 25000, 50000, 100000, 200000],
        },
        validation={"min": 0},
    ),
]

# Combine all questions
ALL_QUESTIONS = QUESTIONS + STANDARD_TIER_QUESTIONS
