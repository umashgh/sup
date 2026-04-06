"""
Advanced Tier — AI Financial Advisor (Asha)

Uses the user's actual numbers from Standard tier calculation to identify
the specific problem and propose quantified, scenario-specific fixes.

Architecture
------------
1. build_context()   — formats user_data + results into structured text
2. detect_problem()  — Python-side analysis (so Claude doesn't have to derive it)
3. build_prompt()    — assembles the full prompt
4. get_advice()      — calls Claude via Bedrock, returns plain text
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

ADVISOR_MODEL = 'us.anthropic.claude-sonnet-4-6-20251101-v1:0'


# ─── Formatting helpers ───────────────────────────────────────────────────────

def _inr(amount):
    """Format a number as Indian currency shorthand."""
    if amount is None:
        return '₹0'
    amount = float(amount)
    if amount >= 10_000_000:
        return f'₹{amount / 10_000_000:.2f}Cr'
    elif amount >= 100_000:
        return f'₹{amount / 100_000:.1f}L'
    elif amount >= 1_000:
        return f'₹{amount / 1_000:.0f}K'
    return f'₹{int(amount)}'


def _months(m):
    if m is None:
        return 'unlimited'
    m = float(m)
    if m >= 24:
        return f'{m / 12:.1f} years'
    return f'{m:.0f} months'


# ─── Problem detection ────────────────────────────────────────────────────────

def detect_problem(results, scenario_type):
    """
    Pre-compute the core problem so the prompt states facts, not questions.
    Returns a dict with problem_type and a human-readable summary string.
    """
    r = results
    depletion = r.get('depletion_year')
    free_up = r.get('free_up_year')
    sustainable = r.get('sustainable', True)
    comfort = r.get('comfort_runway_months')
    target_gap = float(r.get('target_gap') or 0)
    final_corpus = float(r.get('final_corpus') or 0)

    if scenario_type == 'RETIREMENT':
        corpus_gap = float(r.get('corpus_gap') or 0)
        years_to_ret = r.get('years_to_retirement', 0)
        if depletion is not None:
            life_exp = r.get('life_expectancy_years')  # may be None
            shortfall = f'Assets depleted at projection Year {depletion}'
            if life_exp:
                shortfall += f' — {life_exp - depletion} years before life expectancy'
            return {
                'type': 'depletion',
                'summary': shortfall,
                'severity': 'critical' if depletion < 15 else 'moderate',
            }
        if corpus_gap > 0:
            return {
                'type': 'corpus_gap',
                'summary': (
                    f'Corpus shortfall of {_inr(corpus_gap)}. '
                    f'Need {_inr(r.get("required_corpus"))} but have {_inr(r.get("current_corpus"))}. '
                    f'{years_to_ret} years to build the gap.'
                ),
                'severity': 'moderate',
            }
        if not sustainable:
            return {
                'type': 'not_sustainable',
                'summary': 'Corpus survives 20 years but the long-term trajectory is fragile.',
                'severity': 'mild',
            }
        return {
            'type': 'healthy',
            'summary': 'Plan is sustainable — identify optimisation opportunities.',
            'severity': 'none',
        }

    # All other scenarios (FOUNDER, R2I, HALF_FIRE, TERMINATION)
    if comfort is not None and float(comfort) < 12:
        return {
            'type': 'critical_runway',
            'summary': f'Comfort runway is only {_months(comfort)} — dangerously short for this transition.',
            'severity': 'critical',
        }
    if depletion is not None and depletion < 10:
        return {
            'type': 'early_depletion',
            'summary': f'Assets depleted at Year {depletion} in the projection.',
            'severity': 'critical',
        }
    if free_up is None:
        return {
            'type': 'no_fire',
            'summary': 'Financial independence not achieved within the 20-year projection window.',
            'severity': 'moderate',
        }
    if target_gap > 0:
        return {
            'type': 'fire_gap',
            'summary': f'FIRE target gap of {_inr(target_gap)}. Assets not yet at the self-sustaining level.',
            'severity': 'mild',
        }
    return {
        'type': 'healthy',
        'summary': f'Plan looks viable — financial freedom projected at Year {free_up}. Identify optimisations.',
        'severity': 'none',
    }


# ─── Scenario-specific lever hints ───────────────────────────────────────────

_LEVERS = {
    'RETIREMENT': (
        "Possible levers: (a) reduce monthly wants spend, (b) shift more assets from "
        "liquid/semi-liquid to growth equity at higher returns, (c) delay retirement by 1–3 years "
        "to extend accumulation, (d) increase passive income (rental, dividends), "
        "(e) lower safe withdrawal rate."
    ),
    'FOUNDER': (
        "Possible levers: (a) cut personal monthly wants to extend runway, "
        "(b) draw founder salary sooner or adjust the amount, "
        "(c) reduce bootstrap capital committed to the venture, "
        "(d) identify passive income sources to reduce personal burn."
    ),
    'TERMINATION': (
        "Possible levers: (a) cut wants spend during the job-search period, "
        "(b) shorten restart timeline assumptions, "
        "(c) liquidate semi-liquid assets earlier, "
        "(d) increase target restart income to build savings faster post-restart."
    ),
    'R2I': (
        "Possible levers: (a) reduce wants — India cost of living should be lower, "
        "(b) shift overseas assets to higher-return Indian instruments, "
        "(c) plan part-time or consulting income in India, "
        "(d) negotiate rental yield on any property being repatriated."
    ),
    'HALF_FIRE': (
        "Possible levers: (a) increase part-time income target, "
        "(b) reduce monthly wants to close the gap between part-time income and expenses, "
        "(c) shift growth assets to higher-yield instruments, "
        "(d) push Full-FIRE target year back by 1–2 years to allow more compounding."
    ),
}


# ─── Prompt builder ───────────────────────────────────────────────────────────

def build_prompt(user_data, results):
    """
    Assembles a tight, numbers-first prompt for the financial advisor.
    user_data: nested dict with scenario/family/assets/income/profile/rates keys
    results: dict from the Standard calculator
    """
    scenario_type = results.get('scenario_type', 'UNKNOWN')
    s = user_data.get('scenario', {})
    f = user_data.get('family', {})
    a = user_data.get('assets', {})
    inc = user_data.get('income', {})
    prof = user_data.get('profile', {})
    rates = user_data.get('rates', {})

    # Family description
    family_type_map = {
        'solo': 'Single, no dependents',
        'partner': 'With partner',
        'partner_kids': 'Partner + kids',
        'joint': 'Partner + kids + dependent parents',
    }
    family_desc = family_type_map.get(user_data.get('family_type', ''), 'Not specified')

    # Ages
    current_age = s.get('current_age', '?')
    spouse_age = f.get('spouse_age') or s.get('spouse_age')
    age_line = f"Age: {current_age}"
    if spouse_age:
        age_line += f", partner: {spouse_age}"

    # Scenario-specific age framing
    extra_ages = ''
    if scenario_type == 'RETIREMENT':
        ret_age = s.get('retirement_age', '?')
        life_exp = s.get('life_expectancy', '?')
        extra_ages = f"\nRetirement age: {ret_age}  |  Life expectancy: {life_exp}"
        if ret_age != '?' and current_age != '?':
            years_to_ret = int(ret_age) - int(current_age)
            extra_ages += f"  |  Years to retirement: {years_to_ret}"

    # Expenses
    monthly_needs = float(f.get('monthly_needs') or results.get('monthly_needs') or 0)
    monthly_wants = float(f.get('monthly_wants') or 0)
    monthly_total = float(f.get('monthly_expenses') or results.get('monthly_expenses') or 0)
    if monthly_total == 0:
        monthly_total = monthly_needs + monthly_wants

    # Assets
    liquid = float(a.get('liquid') or 0)
    semi_liquid = float(a.get('semi_liquid') or 0)
    growth = float(a.get('growth') or 0)
    property_val = float(a.get('property') or 0)
    total_assets = float(results.get('total_assets') or (liquid + semi_liquid + growth + property_val))
    available = float(results.get('available_cash') or 0)
    emergency = float(results.get('emergency_fund_lock') or 0)

    # Rates
    liq_rate = rates.get('liquid_return_pct', 6)
    semi_rate = rates.get('semi_liquid_return_pct', 8)
    growth_rate = rates.get('growth_return_pct', 12)
    prop_rate = rates.get('property_appreciation_pct', 5)
    needs_inf = rates.get('needs_inflation_pct', 6)
    wants_inf = rates.get('wants_inflation_pct', 7)

    # Income
    passive = float(inc.get('passive_monthly') or results.get('monthly_passive') or 0)
    pension = float(s.get('pension_monthly') or 0)
    pension_age = s.get('pension_start_age', '')

    # Scenario-specific income
    scenario_income_line = ''
    if scenario_type == 'FOUNDER':
        founder_sal = float(s.get('parttime_monthly_income') or 0)
        bootstrap = float(s.get('bootstrap_capital') or 0)
        scenario_income_line = f"\nFounder salary drawn: {_inr(founder_sal)}/month"
        if bootstrap:
            scenario_income_line += f"\nBootstrap capital committed: {_inr(bootstrap)}"
    elif scenario_type in ('R2I', 'HALF_FIRE'):
        parttime = float(s.get('parttime_monthly_income') or 0)
        if parttime:
            scenario_income_line = f"\nPart-time / consulting income: {_inr(parttime)}/month"
    elif scenario_type == 'TERMINATION':
        restart_month = s.get('income_restart_month', 0)
        restart_income = float(s.get('restart_monthly_income') or 0)
        if restart_month:
            scenario_income_line = (
                f"\nExpected restart: Month {restart_month} "
                f"at {_inr(restart_income)}/month"
            )
        severance = float(s.get('severance_lumpsum') or 0)
        if severance:
            scenario_income_line += f"\nSeverance received: {_inr(severance)}"

    # Results
    comfort = results.get('comfort_runway_months')
    austerity = results.get('austerity_runway_months')
    fire_target = float(results.get('target_number') or 0)
    fire_gap = float(results.get('target_gap') or 0)
    depletion = results.get('depletion_year')
    free_up = results.get('free_up_year')
    final_corpus = float(results.get('final_corpus') or 0)
    sustainable = results.get('sustainable', False)

    # Retirement-specific
    required_corpus = float(results.get('required_corpus') or 0)
    corpus_gap = float(results.get('corpus_gap') or 0)
    monthly_savings_needed = float(results.get('monthly_savings_needed') or 0)

    # Problem detection
    problem = detect_problem(results, scenario_type)

    scenario_labels = {
        'FOUNDER': 'Startup Founder Leap',
        'RETIREMENT': 'Retirement Planning',
        'R2I': 'Return to India',
        'HALF_FIRE': 'Half-FIRE / Part-time',
        'TERMINATION': 'Post-Layoff / Job Transition',
    }
    scenario_label = scenario_labels.get(scenario_type, scenario_type)

    prompt = f"""You are Asha, a direct and knowledgeable financial advisor specialising in Indian financial independence planning. Your job is to analyse this specific person's numbers and give concrete, actionable advice. No generic disclaimers. No "consult a professional." Use actual figures from the data below.

═══════════════════════════════
PROFILE: {scenario_label}
═══════════════════════════════
{age_line}{extra_ages}
Family: {family_desc}

MONTHLY EXPENSES
  Needs (essentials): {_inr(monthly_needs)}/month @ {needs_inf}% inflation/yr
  Wants (lifestyle):  {_inr(monthly_wants)}/month @ {wants_inf}% inflation/yr
  Total:              {_inr(monthly_total)}/month

ASSETS TODAY
  Liquid (cash/FDs/savings):    {_inr(liquid)} @ {liq_rate}%/yr
  Semi-liquid (bonds/debt MFs): {_inr(semi_liquid)} @ {semi_rate}%/yr
  Growth (equity/PF/NPS/MFs):   {_inr(growth)} @ {growth_rate}%/yr
  Property:                     {_inr(property_val)} @ {prop_rate}%/yr appreciation
  ─────────────────────────────
  Total assets:                 {_inr(total_assets)}
  Emergency fund locked:        {_inr(emergency)} ({prof.get('emergency_fund_months', 6)} months)
  Available for deployment:     {_inr(available)}

INCOME
  Passive (rent/dividends):     {_inr(passive)}/month{f"{chr(10)}  Pension: {_inr(pension)}/month from age {pension_age}" if pension else ""}{scenario_income_line}

═══════════════════════════════
CALCULATION RESULTS (Standard 20-yr projection)
═══════════════════════════════
  Comfort runway:     {_months(comfort)}
  Austerity runway:   {_months(austerity)}
  FIRE target (25×):  {_inr(fire_target)}
  FIRE gap:           {_inr(fire_gap)}
  Depletion year:     {"Year " + str(depletion) if depletion is not None else "Beyond projection"}
  Financial freedom:  {"Year " + str(free_up) if free_up is not None else "Not within 20 years"}
  Corpus at Year 20:  {_inr(final_corpus)}
  Sustainable:        {"Yes" if sustainable else "No"}{f"{chr(10)}  Required corpus: {_inr(required_corpus)}" if required_corpus else ""}{f"{chr(10)}  Corpus gap: {_inr(corpus_gap)}" if corpus_gap else ""}{f"{chr(10)}  Monthly savings needed: {_inr(monthly_savings_needed)}/month" if monthly_savings_needed else ""}

IDENTIFIED PROBLEM
  {problem['summary']}

{_LEVERS.get(scenario_type, '')}

═══════════════════════════════
YOUR TASK
═══════════════════════════════
Write a response in this exact format — no headings, no markdown, no extra sections:

Paragraph 1 (2–3 sentences): State the core issue using the exact numbers. Be specific about what fails and when.

Paragraph 2 (2–3 sentences): Name the single most impactful fix and its projected outcome in ₹ or years. If the plan is already healthy, name the best optimisation opportunity.

Then 2–3 bullet points (start each with •), each a concrete action the person can take this month or quarter. Use actual ₹ figures. Keep each bullet to one sentence.

Total response: under 150 words. No preamble. No "consult a professional." Use ₹ throughout."""

    return prompt


# ─── Bedrock call ─────────────────────────────────────────────────────────────

def get_advice(user_data, results):
    """
    Calls Claude via Bedrock and returns the advisory text.
    Raises on API or import errors.
    """
    try:
        import anthropic
    except ImportError:
        raise RuntimeError('anthropic package not installed')

    prompt = build_prompt(user_data, results)

    client = anthropic.AnthropicBedrock()
    message = client.messages.create(
        model=ADVISOR_MODEL,
        max_tokens=300,
        messages=[{'role': 'user', 'content': prompt}],
    )

    return message.content[0].text.strip()
