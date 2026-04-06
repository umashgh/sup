"""
Monte Carlo engine for the Advanced tier.

Runs N vectorised 20-year simulations with perturbed annual rates and
random shock expenses. All N paths are computed simultaneously using
NumPy shaped arrays — no Python loop over iterations.

Returns fan chart data (P10/P25/P50/P75/P90) and success statistics.
"""

import numpy as np
from typing import Dict, Optional

# ── Simulation parameters ────────────────────────────────────────────────────
N_DEFAULT        = 2000
PROJECTION_YEARS = 20

# Per-year return standard deviations (around user's base rates)
_SIGMA = {
    'liquid':     0.015,   # FD / savings — low volatility
    'semi':       0.030,   # Debt MFs / bonds
    'growth':     0.180,   # Equity / PF / NPS — high volatility
    'property':   0.080,   # Real estate appreciation
    'needs_inf':  0.020,   # Needs inflation volatility
    'wants_inf':  0.025,   # Wants inflation volatility
    'passive_gr': 0.010,   # Passive income growth volatility
}

# Hard clip bounds (floor, ceiling) for each rate draw
_CLIP = {
    'liquid':     (0.02,  0.10),
    'semi':       (0.02,  0.14),
    'growth':     (-0.15, 0.50),
    'property':   (-0.05, 0.25),
    'needs_inf':  (0.02,  0.15),
    'wants_inf':  (0.02,  0.18),
    'passive_gr': (0.00,  0.10),
}

# Shock expenses: Poisson arrivals × log-normal size
_SHOCK_LAMBDA    = 0.08           # avg 0.08 shocks/yr ≈ one every ~12 yrs
_SHOCK_LOG_MU    = np.log(150_000)  # median shock ≈ ₹1.5L
_SHOCK_LOG_SIGMA = 1.0            # 90th-pct shock ≈ ₹9L


class MonteCarloEngine:
    """
    Vectorised Monte Carlo simulator.

    Usage:
        engine = MonteCarloEngine(user_data, scenario_type)
        results = engine.run(n=2000)
    """

    def __init__(self, user_data: Dict, scenario_type: str):
        self.user_data     = user_data
        self.scenario_type = scenario_type
        self._load_inputs()

    # ================================================================
    #  Input loading
    # ================================================================

    def _load_inputs(self):
        u = self.user_data
        r = u.get('rates', {})

        # Base rates (from user overrides or defaults; as_dict() gives decimals)
        self.base = {
            'liquid':     float(r.get('liquid_return',          0.06)),
            'semi':       float(r.get('semi_liquid_return',     0.08)),
            'growth':     float(r.get('growth_return',          0.12)),
            'property':   float(r.get('property_appreciation',  0.05)),
            'prop_yield': float(r.get('property_rental_yield',  0.03)),
            'needs_inf':  float(r.get('needs_inflation',        0.06)),
            'wants_inf':  float(r.get('wants_inflation',        0.07)),
            'passive_gr': float(r.get('passive_growth',         0.04)),
        }

        f   = u.get('family',   {})
        a   = u.get('assets',   {})
        inc = u.get('income',   {})
        p   = u.get('profile',  {})
        s   = u.get('scenario', {})

        self.monthly_expenses = float(f.get('monthly_expenses', 0) or 0)
        needs_pct             = 0.6
        self.monthly_needs    = float(f.get('monthly_needs') or self.monthly_expenses * needs_pct)
        self.monthly_wants    = float(f.get('monthly_wants') or self.monthly_expenses * (1 - needs_pct))

        self.liq  = float(a.get('liquid',      0) or 0)
        self.semi = float(a.get('semi_liquid', 0) or 0)
        self.grow = float(a.get('growth',      0) or 0)
        self.prop = float(a.get('property',    0) or 0)

        self.monthly_passive  = float(inc.get('passive_monthly', 0) or 0)
        self.emergency_months = int(p.get('emergency_fund_months', 6) or 6)
        self.one_time_upfront = float(f.get('one_time_expenses', 0) or 0)

        self.emergency_lock = self.monthly_needs * self.emergency_months
        self.total_assets   = self.liq + self.semi + self.grow + self.prop

        self._load_scenario_inputs(s)

    def _load_scenario_inputs(self, s: dict):
        """Extract scenario-specific fields (mirrors standard calculator hooks)."""
        self.bootstrap              = 0.0
        self.scenario_annual_salary = 0.0
        self.salary_start_year      = 0
        self.gratuity               = 0.0
        self.gratuity_year: Optional[int] = None
        self.pension_annual         = 0.0
        self.pension_start_year: Optional[int] = None

        sc = self.scenario_type

        if sc == 'FOUNDER':
            bootstrapped = s.get('venture_bootstrapped', False)
            self.bootstrap              = float(s.get('bootstrap_capital', 0) or 0) if bootstrapped else 0
            self.scenario_annual_salary = float(s.get('parttime_monthly_income', 0) or 0) * 12
            self.salary_start_year      = int(s.get('founder_salary_start_month', 0) or 0) // 12

        elif sc == 'RETIREMENT':
            current_age       = int(s.get('current_age', 30)    or 30)
            retirement_age    = int(s.get('retirement_age', 60)  or 60)
            pension_start_age = int(s.get('pension_start_age', retirement_age) or retirement_age)
            self.gratuity           = float(s.get('gratuity_lumpsum', 0) or 0)
            self.gratuity_year      = max(0, retirement_age - current_age)
            self.pension_annual     = float(s.get('pension_monthly', 0) or 0) * 12
            self.pension_start_year = max(0, pension_start_age - current_age)

        elif sc in ('R2I', 'HALF_FIRE'):
            self.scenario_annual_salary = float(s.get('parttime_monthly_income', 0) or 0) * 12
            self.salary_start_year      = 0

        elif sc == 'TERMINATION':
            self.gratuity               = float(s.get('severance_lumpsum', 0) or 0)
            self.gratuity_year          = 0
            restart_month               = int(s.get('income_restart_month', 0) or 0)
            self.scenario_annual_salary = float(s.get('restart_monthly_income', 0) or 0) * 12
            self.salary_start_year      = restart_month // 12

    # ================================================================
    #  Main run
    # ================================================================

    def run(self, n: int = N_DEFAULT) -> Dict:
        N, Y = n, PROJECTION_YEARS
        rng  = np.random.default_rng()

        # ── 1. Per-year rate draws: shape (N, Y) ─────────────────────────
        def draw(key) -> np.ndarray:
            return rng.normal(self.base[key], _SIGMA[key], (N, Y)).clip(*_CLIP[key])

        liquid_r   = draw('liquid')
        semi_r     = draw('semi')
        growth_r   = draw('growth')
        # Property total return = appreciation + rental yield
        prop_r     = draw('property') + self.base['prop_yield']
        needs_inf  = draw('needs_inf')
        wants_inf  = draw('wants_inf')
        passive_gr = draw('passive_gr')

        # ── 2. Random shock expenses: shape (N, Y) ───────────────────────
        shocks = (
            rng.poisson(_SHOCK_LAMBDA, (N, Y)) *
            rng.lognormal(_SHOCK_LOG_MU, _SHOCK_LOG_SIGMA, (N, Y))
        )

        # ── 3. Blended portfolio return: shape (N, Y) ────────────────────
        #  Weight by initial allocation after deducting locked/deployed capital.
        initial_corpus = max(
            0.0,
            self.total_assets - self.emergency_lock - self.bootstrap - self.one_time_upfront
        )
        denom = max(initial_corpus, 0.01)
        w_liq  = max(0.0, self.liq - self.emergency_lock) / denom
        w_semi = self.semi / denom
        w_grow = self.grow / denom
        w_prop = self.prop / denom
        total_w = w_liq + w_semi + w_grow + w_prop
        if total_w > 0:
            w_liq /= total_w; w_semi /= total_w; w_grow /= total_w; w_prop /= total_w

        portfolio_r = (
            w_liq  * liquid_r +
            w_semi * semi_r   +
            w_grow * growth_r +
            w_prop * prop_r
        )  # (N, Y)

        # ── 4. Cumulative inflation multipliers: shape (N, Y+1) ──────────
        ones         = np.ones((N, 1))
        needs_mult   = np.hstack([ones, np.cumprod(1 + needs_inf,  axis=1)])
        wants_mult   = np.hstack([ones, np.cumprod(1 + wants_inf,  axis=1)])
        passive_mult = np.hstack([ones, np.cumprod(1 + passive_gr, axis=1)])

        # ── 5. Annual income / expense streams ───────────────────────────
        annual_passive  = self.monthly_passive * 12 * passive_mult   # (N, Y+1)
        annual_needs    = self.monthly_needs   * 12 * needs_mult      # (N, Y+1)
        annual_wants    = self.monthly_wants   * 12 * wants_mult      # (N, Y+1)

        # Deterministic scenario income (salary, pension) — broadcast (1, Y+1) → (N, Y+1)
        scen_inc    = self._build_scenario_income(Y)    # (Y+1,)
        pension_inc = self._build_pension_income(Y)     # (Y+1,)

        total_income_arr  = annual_passive + scen_inc[None, :] + pension_inc[None, :]
        total_expense_arr = annual_needs   + annual_wants

        # ── 6. Gratuity / severance injection: (Y+1,) ───────────────────
        gratuity_arr = np.zeros(Y + 1)
        if self.gratuity > 0 and self.gratuity_year is not None:
            gratuity_arr[min(self.gratuity_year, Y)] = self.gratuity

        # ── 7. Projection loop: shape (N, Y+1) ───────────────────────────
        corpus       = np.zeros((N, Y + 1))
        corpus[:, 0] = initial_corpus

        for yr in range(Y):
            net = (
                total_income_arr[:, yr]
                - total_expense_arr[:, yr]
                - shocks[:, yr]
                + gratuity_arr[yr]
            )
            corpus[:, yr + 1] = np.maximum(
                0.0,
                corpus[:, yr] * (1 + portfolio_r[:, yr]) + net
            )

        return self._compute_results(corpus, total_income_arr, total_expense_arr, N, Y)

    # ================================================================
    #  Helpers
    # ================================================================

    def _build_scenario_income(self, Y: int) -> np.ndarray:
        arr = np.zeros(Y + 1)
        if self.scenario_annual_salary > 0:
            gr = self.base['passive_gr']
            for yr in range(self.salary_start_year, Y + 1):
                arr[yr] = self.scenario_annual_salary * ((1 + gr) ** (yr - self.salary_start_year))
        return arr

    def _build_pension_income(self, Y: int) -> np.ndarray:
        arr = np.zeros(Y + 1)
        if self.pension_annual > 0 and self.pension_start_year is not None:
            for yr in range(self.pension_start_year, Y + 1):
                arr[yr] = self.pension_annual * (1.04 ** (yr - self.pension_start_year))
        return arr

    # ================================================================
    #  Results
    # ================================================================

    def _compute_results(
        self,
        corpus: np.ndarray,
        total_income_arr: np.ndarray,
        total_expense_arr: np.ndarray,
        N: int,
        Y: int,
    ) -> Dict:
        # ── Success rate ─────────────────────────────────────────────────
        success_rate = float(np.mean(corpus[:, -1] > 0)) * 100

        # ── Fan chart percentiles at each year ───────────────────────────
        pcts = np.percentile(corpus, [10, 25, 50, 75, 90], axis=0)  # (5, Y+1)
        p10, p25, p50, p75, p90 = pcts

        final = corpus[:, -1]

        # ── Depletion stats ──────────────────────────────────────────────
        is_depleted  = corpus <= 0                       # (N, Y+1)
        depletion_yr = np.argmax(is_depleted, axis=1)   # first zero index per path
        never        = ~np.any(is_depleted, axis=1)
        depletion_yr = np.where(never, Y + 1, depletion_yr)

        pct_surviving = [
            round(float(np.mean(depletion_yr > yr)) * 100, 1)
            for yr in range(Y + 1)
        ]

        # ── Free-up year (income >= expenses) ────────────────────────────
        income_covers  = total_income_arr >= total_expense_arr   # (N, Y+1)
        free_up_idx    = np.argmax(income_covers, axis=1)
        any_free_up    = np.any(income_covers, axis=1)
        free_up_idx    = np.where(any_free_up, free_up_idx, Y + 1)
        achieving      = free_up_idx[free_up_idx <= Y]
        median_free_up = int(np.median(achieving)) if len(achieving) > 0 else None
        pct_achieve    = round(float(len(achieving) / N) * 100, 1)

        years_labels = [f"Year {i}" for i in range(Y + 1)]

        return {
            'success_rate':        round(success_rate, 1),
            'pct_surviving':       pct_surviving,
            'median_free_up_year': median_free_up,
            'pct_achieve_free_up': pct_achieve,
            'p10_final':           round(float(np.percentile(final, 10)), 0),
            'p50_final':           round(float(np.percentile(final, 50)), 0),
            'p90_final':           round(float(np.percentile(final, 90)), 0),
            'fan_chart': {
                'years': years_labels,
                'p10':   [round(float(v), 0) for v in p10],
                'p25':   [round(float(v), 0) for v in p25],
                'p50':   [round(float(v), 0) for v in p50],
                'p75':   [round(float(v), 0) for v in p75],
                'p90':   [round(float(v), 0) for v in p90],
            },
            'n_iterations':  N,
            'scenario_type': self.scenario_type,
            'tier':          'ADVANCED',
        }
