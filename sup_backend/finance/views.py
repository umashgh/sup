from rest_framework import viewsets, permissions
from .models import (
    AssetMaster, IncomeMaster, ExpenseMaster,
    FamilyProfile, FamilyMember, Asset, Income, Expense
)
from .serializers import (
    AssetMasterSerializer, IncomeMasterSerializer, ExpenseMasterSerializer,
    FamilyProfileSerializer, FamilyMemberSerializer, AssetSerializer, IncomeSerializer, ExpenseSerializer
)

class BaseUserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# --- Master Data Views ---

class AssetMasterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssetMaster.objects.all()
    serializer_class = AssetMasterSerializer
    permission_classes = [permissions.AllowAny] # Or IsAuthenticated

class IncomeMasterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IncomeMaster.objects.all()
    serializer_class = IncomeMasterSerializer
    permission_classes = [permissions.AllowAny]

class ExpenseMasterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExpenseMaster.objects.all()
    serializer_class = ExpenseMasterSerializer
    permission_classes = [permissions.AllowAny]

# --- User Data Views ---

from rest_framework.decorators import action
from rest_framework.response import Response

class FamilyProfileViewSet(BaseUserViewSet):
    queryset = FamilyProfile.objects.all()
    serializer_class = FamilyProfileSerializer

    @action(detail=True, methods=['post'])
    def calculate_defaults(self, request, pk=None):
        profile = self.get_object()
        members = FamilyMember.objects.filter(user=profile.user)
        
        # Base Split
        needs = 50
        wants = 30
        savings = 20
        
        # Adjustments
        has_school_age_child = members.filter(member_type='child', age__gte=4, age__lte=21).exists()
        has_dependent_adult = members.filter(member_type='dependent_adult').exists()
        
        if has_school_age_child:
            needs += 10
            wants -= 5
            savings -= 5
            
        if has_dependent_adult:
            needs += 5
            wants -= 5
            # Savings stays same or reduce wants further? Domain says reduce wants.
            
        # Normalize if > 100 (simple clamp for now)
        total = needs + wants + savings
        if total != 100:
            # Adjust wants to balance
            wants = 100 - needs - savings
            
        profile.needs_percent = needs
        profile.wants_percent = wants
        profile.savings_percent = savings
        profile.save()
        
        return Response(FamilyProfileSerializer(profile).data)

    @action(detail=False, methods=['get'])
    def project(self, request):
        # Basic projection logic based on profile levels and assets
        profile = self.get_queryset().first()
        if not profile:
            return Response([])

        # Query Params
        austerity_mode = request.query_params.get('austerity', 'false').lower() == 'true'
        emergency_months = int(request.query_params.get('emergency_months', profile.emergency_fund_months))

        # Determine base values from levels if no specific data
        # Wealth Level: 1 (<2Cr), 2 (2-10Cr), 3 (>10Cr)
        base_assets = {1: 5000000, 2: 50000000, 3: 150000000}.get(profile.wealth_level, 1000000)
        
        # Income Level: 1 (<20L), 2 (20-50L), 3 (>50L)
        base_income = {1: 1500000, 2: 3500000, 3: 7500000}.get(profile.income_level, 1500000)
        
        # Expense Level: 1 (<20L), 2 (20-50L), 3 (>50L)
        base_expense = {1: 1200000, 2: 3000000, 3: 6000000}.get(profile.expense_level, 1200000)

        # Adjust with specific assets if any
        user_assets = Asset.objects.filter(user=request.user)
        pledged_assets_value = 0
        
        if user_assets.exists():
            # Only count non-pledged assets for Family Runway base
            personal_assets = sum(a.initial_value for a in user_assets if not a.is_business_pledged)
            pledged_assets_value = float(sum(a.initial_value for a in user_assets if a.is_business_pledged))
            base_assets = float(personal_assets)
        
        years = range(2024, 2045)
        data = []
        
        current_assets = base_assets
        
        # Split ratios
        needs_ratio = profile.needs_percent / 100.0
        wants_ratio = profile.wants_percent / 100.0
        
        for year in years:
            # Simple assumptions:
            # Assets grow at 8%
            # Expenses grow at 6% (inflation)
            # Income grows at 5% until 2035 (retirement?), then 0
            
            current_income = base_income * (1.05 ** (year - 2024)) if year < 2035 else 0
            base_year_expense = base_expense * (1.06 ** (year - 2024))
            
            # Apply splits
            expense_needs = base_year_expense * needs_ratio
            expense_wants = base_year_expense * wants_ratio
            
            # Apply Austerity if requested
            if austerity_mode:
                # Cut wants by 50%
                expense_wants = expense_wants * 0.5
                
            current_expense = expense_needs + expense_wants
            
            # Emergency Fund Calculation
            monthly_expense = current_expense / 12
            emergency_fund_locked = monthly_expense * emergency_months
            
            investable_assets = max(0, current_assets - emergency_fund_locked)
            
            asset_growth = investable_assets * 0.08
            # Passive income assumption: 4% withdrawal rate safe from investable assets
            passive_income = investable_assets * 0.04
            
            # Grow pledged assets separately (assuming they are invested but locked)
            pledged_growth = pledged_assets_value * 0.08
            pledged_assets_value += pledged_growth

            net_flow = current_income - current_expense
            current_assets += net_flow + asset_growth
            
            data.append({
                'year': year,
                'assets': round(current_assets, 2),
                'investable_assets': round(investable_assets, 2),
                'emergency_fund': round(emergency_fund_locked, 2),
                'pledged_assets': round(pledged_assets_value, 2),
                'income': round(current_income, 2),
                'passive_income': round(passive_income, 2),
                'expenses': round(current_expense, 2),
                'expenses_needs': round(expense_needs, 2),
                'expenses_wants': round(expense_wants, 2),
            })
            
        return Response(data)

class FamilyMemberViewSet(BaseUserViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer

class AssetViewSet(BaseUserViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

class IncomeViewSet(BaseUserViewSet):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer

class ExpenseViewSet(BaseUserViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
