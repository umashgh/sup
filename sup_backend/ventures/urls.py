from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VentureViewSet, StartupCostViewSet, FounderSalaryViewSet

router = DefaultRouter()
router.register(r'ventures', VentureViewSet)
router.register(r'costs', StartupCostViewSet)
router.register(r'salaries', FounderSalaryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
