from django.db import models
from django.contrib.auth.models import User


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

    class Meta:
        verbose_name = "Scenario Profile"
        verbose_name_plural = "Scenario Profiles"

    def __str__(self):
        return f"{self.user.username} - {self.get_scenario_type_display()}"
