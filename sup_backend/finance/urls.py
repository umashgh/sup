from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AssetMasterViewSet, IncomeMasterViewSet, ExpenseMasterViewSet,
    FamilyProfileViewSet, FamilyMemberViewSet, AssetViewSet, IncomeViewSet, ExpenseViewSet
)

router = DefaultRouter()
router.register(r'masters/assets', AssetMasterViewSet)
router.register(r'masters/incomes', IncomeMasterViewSet)
router.register(r'masters/expenses', ExpenseMasterViewSet)
router.register(r'profile', FamilyProfileViewSet)
router.register(r'members', FamilyMemberViewSet)
router.register(r'assets', AssetViewSet)
router.register(r'incomes', IncomeViewSet)
router.register(r'expenses', ExpenseViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
