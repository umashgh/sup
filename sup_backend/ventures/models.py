from django.db import models
from django.contrib.auth.models import User

class Venture(models.Model):
    STAGE_CHOICES = [
        ('idea', 'Idea'),
        ('mvp', 'MVP'),
        ('growth', 'Growth'),
        ('scaling', 'Scaling'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='idea')
    target_runway_months = models.IntegerField(default=12)
    business_failure_probability = models.DecimalField(max_digits=5, decimal_places=2, default=0.50) # 50% chance by default

    def __str__(self):
        return self.name

class StartupCost(models.Model):
    venture = models.ForeignKey(Venture, on_delete=models.CASCADE, related_name='costs')
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    frequency = models.CharField(max_length=20, default='one_time') # monthly, annual, one_time
    
    def __str__(self):
        return f"{self.name} ({self.venture.name})"

class FounderSalary(models.Model):
    venture = models.ForeignKey(Venture, on_delete=models.CASCADE, related_name='salaries')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    start_month_offset = models.IntegerField(default=0) # Months from venture start
    end_month_offset = models.IntegerField(default=12) # Months from venture start
    
    def __str__(self):
        return f"Salary {self.amount} ({self.start_month_offset}-{self.end_month_offset})"
