from datetime import datetime
from django.db import models
from django.contrib.auth.models import User


def _current_year():
    return datetime.now().year


def _current_year_plus_20():
    return datetime.now().year + 20

# --- Master Data Models ---

class AssetMaster(models.Model):
    CATEGORY_CHOICES = [
        ('financial', 'Financial'),
        ('real_estate', 'Real Estate'),
        ('retirals', 'Retirals'),
        ('others', 'Others'),
    ]
    UNCERTAINTY_CHOICES = [
        ('none', 'None'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('volatile', 'Volatile'),
    ]
    
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    number_level = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3')])
    typical_initial_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    appreciation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    typical_return_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    uncertainty_level = models.CharField(max_length=20, choices=UNCERTAINTY_CHOICES, default='none')
    basis = models.CharField(max_length=20, default='single') # single/per unit
    liquid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} (L{self.number_level})"

class IncomeMaster(models.Model):
    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('asset_return', 'Asset Return'),
        ('others', 'Others'),
    ]
    UNCERTAINTY_CHOICES = [
        ('none', 'None'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('volatile', 'Volatile'),
    ]
    
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    number_level = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3')])
    typical_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    frequency = models.CharField(max_length=20, default='annual')
    growth_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    efficiency_pct = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    uncertainty_level = models.CharField(max_length=20, choices=UNCERTAINTY_CHOICES, default='none')

    def __str__(self):
        return f"{self.name} (L{self.number_level})"

class ExpenseMaster(models.Model):
    PERTAINS_TO_CHOICES = [
        ('household', 'Household'),
        ('adult', 'Adult'),
        ('child', 'Child'),
        ('house', 'House'),
        ('vehicle', 'Vehicle'),
        ('pet', 'Pet'),
        ('dependent_adult', 'Dependent Adult'),
        ('others', 'Others'),
    ]
    UNCERTAINTY_CHOICES = [
        ('none', 'None'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('volatile', 'Volatile'),
    ]
    BUDGET_TYPE_CHOICES = [
        ('needs', 'Needs (Survival)'),
        ('wants', 'Wants (Lifestyle)'),
        ('savings', 'Savings/Investments'),
    ]
    
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE_CHOICES, default='needs')
    number_level = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3')])
    pertains_to = models.CharField(max_length=50, choices=PERTAINS_TO_CHOICES, default='household')
    typical_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    frequency = models.CharField(max_length=20, default='annual')
    inflation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    insurance_indicator = models.BooleanField(default=False)
    copay_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    uncertainty_level = models.CharField(max_length=20, choices=UNCERTAINTY_CHOICES, default='none')

    def __str__(self):
        return f"{self.name} (L{self.number_level})"

# --- User Data Models ---

class FamilyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    scenario = models.ForeignKey('core.ScenarioProfile', on_delete=models.CASCADE, null=True, blank=True, related_name='family_profile')
    modelling_start_year = models.IntegerField(default=_current_year)
    modelling_end_year = models.IntegerField(default=_current_year_plus_20)
    bank_rate = models.DecimalField(max_digits=5, decimal_places=2, default=6.0)
    wealth_level = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3')], default=1)
    income_level = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3')], default=1)
    expense_level = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3')], default=1)
    rented_house = models.BooleanField(default=False)
    financial_investment_areas = models.JSONField(default=list, blank=True)
    physical_investment_areas = models.JSONField(default=list, blank=True)
    
    num_houses = models.IntegerField(default=1)
    num_vehicles = models.IntegerField(default=1)
    has_pet = models.BooleanField(default=False)

    # Founder FIRE specific
    emergency_fund_months = models.IntegerField(default=6)
    needs_percent = models.IntegerField(default=50)
    wants_percent = models.IntegerField(default=30)
    savings_percent = models.IntegerField(default=20)
    has_private_health_insurance = models.BooleanField(default=False)
    pause_retirals = models.BooleanField(default=False)

    # Flow progression
    current_tier = models.IntegerField(default=1)  # 1=quick, 2=buckets, 3=deep dive

    def __str__(self):
        return f"{self.user.username}'s Profile"

class FamilyMember(models.Model):
    MEMBER_TYPE_CHOICES = [
        ('earning_adult', 'Earning Adult'),
        ('dependent_adult', 'Dependent Adult'),
        ('child', 'Child'),
        ('pet', 'Pet'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    member_type = models.CharField(max_length=50, choices=MEMBER_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    retirement_age = models.IntegerField(default=60, null=True, blank=True)
    has_pf = models.BooleanField(default=False)
    health_insurance = models.BooleanField(default=False)
    allowance = models.DecimalField(max_digits=15, decimal_places=2, default=0, null=True, blank=True)
    age_of_graduation_start = models.IntegerField(default=18, null=True, blank=True)
    age_of_expenses_end = models.IntegerField(default=24, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.member_type})"

class Asset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    initial_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    appreciation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    return_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    swp_possible = models.BooleanField(default=False)
    uncertainty_level = models.CharField(max_length=20, default='none')
    liquid = models.BooleanField(default=False)
    
    # Founder FIRE specific
    is_business_pledged = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    typical_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    frequency = models.CharField(max_length=20, default='annual')
    growth_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    efficiency_pct = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    uncertainty_level = models.CharField(max_length=20, default='none')
    linked_asset = models.ForeignKey('Asset', on_delete=models.SET_NULL, null=True, blank=True)
    withdrawal_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return self.name

class Expense(models.Model):
    BUDGET_TYPE_CHOICES = [
        ('needs', 'Needs (Survival)'),
        ('wants', 'Wants (Lifestyle)'),
        ('savings', 'Savings/Investments'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE_CHOICES, default='needs')
    pertains_to = models.CharField(max_length=50, default='household')
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    typical_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    frequency = models.CharField(max_length=20, default='annual')
    inflation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    insurance_indicator = models.BooleanField(default=False)
    copay_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    uncertainty_level = models.CharField(max_length=20, default='none')

    def __str__(self):
        return self.name


# --- Calculation Results ---

class CashflowProjection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField()
    total_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    income_splits = models.JSONField(default=dict, blank=True)
    total_expense = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expense_needs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expense_wants = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_cashflow = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_assets = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    excess_cashflow = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    shortfall = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    observations = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['year']
        unique_together = ['user', 'year']

    def __str__(self):
        return f"{self.user.username} - {self.year}"
