from django.urls import path
from . import views

urlpatterns = [
    # New mobile-first pages at root
    path('', views.scenario_selector_page, name='scenario_selector'),
    path('questions/', views.questions_flow_page, name='questions_flow'),
    path('results/', views.results_page, name='results'),

    # Guest login
    path('start/', views.guest_login, name='guest_login'),

    # New scenario-based API endpoints
    path('api/scenarios/select/', views.select_scenario, name='select_scenario'),
    path('api/scenarios/questions/', views.get_next_questions, name='get_next_questions'),
    path('api/scenarios/compute-expenses/', views.compute_expenses_view, name='compute_expenses'),
    path('api/scenarios/calculate/', views.calculate_tier, name='calculate_tier'),
    path('api/scenarios/advance-tier/', views.advance_tier, name='advance_tier'),
    path('api/scenarios/rates/', views.rate_preferences, name='rate_preferences'),
    path('api/scenarios/advise/', views.advise, name='advise'),
    path('api/scenarios/monte-carlo/', views.monte_carlo, name='monte_carlo'),
    path('api/scenarios/restore/', views.restore_flow_state, name='restore_flow_state'),
    path('api/track/', views.track_event, name='track_event'),
    path('health/', views.health_check, name='health_check'),
    path('ops/', views.ops_page, name='ops_page'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]
