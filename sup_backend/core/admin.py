from django.contrib import admin
from .models import ScenarioProfile


@admin.register(ScenarioProfile)
class ScenarioProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario_type', 'created_at')
    list_filter = ('scenario_type', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
