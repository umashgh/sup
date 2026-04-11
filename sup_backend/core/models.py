from django.db import models
from django.contrib.auth.models import User


class UserRatePreferences(models.Model):
    """
    Per-user overrides for the financial rate assumptions used in projections.
    All fields default to the standard Indian market assumptions.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rate_prefs')

    # Asset return rates (% per year)
    liquid_return_pct = models.DecimalField(max_digits=5, decimal_places=2, default=6.00)
    semi_liquid_return_pct = models.DecimalField(max_digits=5, decimal_places=2, default=8.00)
    growth_return_pct = models.DecimalField(max_digits=5, decimal_places=2, default=12.00)
    property_appreciation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    property_rental_yield_pct = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)

    # Inflation & growth rates (% per year)
    needs_inflation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=6.00)
    wants_inflation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=7.00)
    passive_growth_pct = models.DecimalField(max_digits=5, decimal_places=2, default=4.00)

    # Safe withdrawal rate for free_up_year check (% of financial assets)
    swr_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, default=4.00)

    class Meta:
        verbose_name = "User Rate Preferences"

    def __str__(self):
        return f"{self.user.username} — rate prefs"

    def as_dict(self):
        return {
            'liquid_return': float(self.liquid_return_pct) / 100,
            'semi_liquid_return': float(self.semi_liquid_return_pct) / 100,
            'growth_return': float(self.growth_return_pct) / 100,
            'property_appreciation': float(self.property_appreciation_pct) / 100,
            'property_rental_yield': float(self.property_rental_yield_pct) / 100,
            'needs_inflation': float(self.needs_inflation_pct) / 100,
            'wants_inflation': float(self.wants_inflation_pct) / 100,
            'passive_growth': float(self.passive_growth_pct) / 100,
            'swr_rate': float(self.swr_rate_pct) / 100,
        }

    def as_pct_dict(self):
        """Return rates as percentages (for display)."""
        return {
            'liquid_return_pct': float(self.liquid_return_pct),
            'semi_liquid_return_pct': float(self.semi_liquid_return_pct),
            'growth_return_pct': float(self.growth_return_pct),
            'property_appreciation_pct': float(self.property_appreciation_pct),
            'property_rental_yield_pct': float(self.property_rental_yield_pct),
            'needs_inflation_pct': float(self.needs_inflation_pct),
            'wants_inflation_pct': float(self.wants_inflation_pct),
            'passive_growth_pct': float(self.passive_growth_pct),
            'swr_rate_pct': float(self.swr_rate_pct),
        }


class BehaviourEvent(models.Model):
    """
    Anonymous session-level behaviour tracking.
    No PII — keyed only on Django's session_key.
    """
    session_key = models.CharField(max_length=64, db_index=True)
    event       = models.CharField(max_length=64, db_index=True)
    properties  = models.JSONField(default=dict)
    ts          = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session_key', 'ts']),
            models.Index(fields=['event', 'ts']),
        ]

    def __str__(self):
        return f"{self.event} [{self.session_key[:8]}] @ {self.ts:%Y-%m-%d %H:%M}"


class UserEncryption(models.Model):
    """
    Tracks per-user passphrase-based encryption.
    The passphrase is NEVER stored — only a salt and a verification token derived from it.
    All user data is stored as an encrypted JSON payload; original model fields are cleared.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='encryption')
    kdf_salt = models.CharField(max_length=64)          # hex-encoded 32-byte PBKDF2 salt
    passphrase_hint = models.CharField(max_length=200, blank=True, default='')
    verification_token = models.TextField()             # Fernet-encrypted b'SALARYFREE_VERIFIED'
    encrypted_payload = models.TextField()              # Fernet-encrypted JSON of all user data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Encryption"

    def __str__(self):
        return f"{self.user.username} — encrypted"


class ScenarioProfile(models.Model):
    """
    Stores scenario-specific data for each user.
    Only includes fields that directly impact financial calculations.
    """
    SCENARIO_TYPES = [
        ('FOUNDER', 'Startup Founder'),
        ('RETIREMENT', 'Retirement Planning'),
        ('R2I', 'Returning to India'),
        ('HALF_FIRE', 'Half FIRE / Part-time'),
        ('TERMINATION', 'Job Loss / Severance'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='scenario_profile')
    scenario_type = models.CharField(max_length=20, choices=SCENARIO_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Retirement specific
    current_age = models.IntegerField(null=True, blank=True)
    retirement_age = models.IntegerField(null=True, blank=True)
    life_expectancy = models.IntegerField(null=True, blank=True)
    pension_monthly = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pension_start_age = models.IntegerField(null=True, blank=True)
    gratuity_lumpsum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Half FIRE specific
    current_monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    parttime_monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    parttime_start_month = models.IntegerField(null=True, blank=True, help_text="Months from now")
    full_fire_target_month = models.IntegerField(null=True, blank=True, help_text="Months from now")

    # Termination specific
    severance_lumpsum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    severance_month_count = models.IntegerField(null=True, blank=True, help_text="Months of salary")
    income_restart_month = models.IntegerField(null=True, blank=True, help_text="Months from now when income restarts")
    restart_monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Salary after restart")

    # Founder specific
    venture_bootstrapped = models.BooleanField(default=False, null=True, blank=True)
    bootstrap_capital = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    founder_salary_start_month = models.IntegerField(
        null=True, blank=True,
        help_text="Months from now when founder starts drawing salary from the venture"
    )

    class Meta:
        verbose_name = "Scenario Profile"
        verbose_name_plural = "Scenario Profiles"

    def __str__(self):
        return f"{self.user.username} - {self.get_scenario_type_display()}"
