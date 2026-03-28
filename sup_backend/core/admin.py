from django.contrib import admin
from .models import ScenarioProfile, UserRatePreferences


@admin.register(ScenarioProfile)
class ScenarioProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario_type', 'created_at')
    list_filter = ('scenario_type', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserRatePreferences)
class UserRatePreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'liquid_return_pct', 'growth_return_pct', 'needs_inflation_pct', 'swr_rate_pct')
    search_fields = ('user__username',)
