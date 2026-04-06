import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from finance.models import (
    FamilyProfile, FamilyMember, Asset, Income, Expense, CashflowProjection
)


def guest_login(request):
    """Create a guest user, log them in via session, redirect to main flow."""
    # Don't create a new session if already authenticated
    if request.user.is_authenticated:
        return redirect('scenario_selector')

    username = f"guest_{uuid.uuid4().hex[:12]}"
    user = User.objects.create_user(username=username)
    login(request, user, backend='core.backends.UsernameOnlyBackend')
    FamilyProfile.objects.create(user=user)

    # Support both AJAX and regular requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.META.get('HTTP_ACCEPT', '').find('application/json') != -1:
        from django.middleware.csrf import get_token
        return JsonResponse({'success': True, 'username': username, 'csrfToken': get_token(request)})
    return redirect('scenario_selector')


# ============================================================================
# NEW MOBILE-FIRST PAGES
# ============================================================================

def scenario_selector_page(request):
    """Mobile-first scenario selection page."""
    return render(request, 'scenario_selector.html')


@login_required
def questions_flow_page(request):
    """Mobile-first dynamic questions flow page."""
    return render(request, 'questions_flow.html')


@login_required
def results_page(request):
    """Mobile-first results display page."""
    return render(request, 'results.html')


@require_POST
@login_required
def calculate(request):
    """
    Tier 2 projection endpoint.
    Accepts all Tier 1+2 inputs, saves profile data,
    runs a year-by-year projection, returns chart data + free-up year.
    """
    data = json.loads(request.body)
    user = request.user
    profile, _ = FamilyProfile.objects.get_or_create(user=user)

    # --- Save profile from Tier 1 inputs ---
    family_type = data.get('family_type', 'Just me')
    profile.wealth_level = data.get('wealth_level', 1)
    profile.income_level = data.get('income_level', 1)
    profile.expense_level = data.get('expense_level', 1)
    profile.emergency_fund_months = data.get('emergency_months', 6)
    profile.current_tier = 2
    profile.save()

    # --- Save family members ---
    FamilyMember.objects.filter(user=user).delete()

    # Primary earner
    FamilyMember.objects.create(
        user=user, member_type='earning_adult', name='Self', age=30
    )

    if family_type in ('With partner', 'Partner + kids', 'Joint family'):
        FamilyMember.objects.create(
            user=user, member_type='earning_adult', name='Partner', age=30
        )

    if family_type == 'Partner + kids':
        kid_ages = data.get('kid_ages', [5])
        for i, age in enumerate(kid_ages):
            FamilyMember.objects.create(
                user=user, member_type='child',
                name=f'Child {i + 1}', age=age
            )

    if family_type == 'Joint family':
        num_dep = data.get('num_dependents', 1)
        for i in range(num_dep):
            FamilyMember.objects.create(
                user=user, member_type='dependent_adult',
                name=f'Dependent {i + 1}', age=65
            )

    # --- Extract financial inputs ---
    monthly_survival = float(data.get('monthly_survival', 0))
    monthly_lifestyle = float(data.get('monthly_lifestyle', 0))
    dependent_cost = float(data.get('dependent_cost', 0))
    liquid_savings = float(data.get('liquid_savings', 0))
    monthly_passive = float(data.get('monthly_passive', 0))
    emergency_months = int(data.get('emergency_months', 6))

    semi_liquid = float(data.get('semi_liquid_assets', 0))
    growth = float(data.get('growth_assets', 0))
    prop = float(data.get('property_assets', 0))
    expected_return_pct = float(data.get('expected_return', 12)) / 100.0

    big_expenses = data.get('big_expenses', [])
    has_side_income = data.get('has_side_income', False)
    side_income_amount = float(data.get('side_income_amount', 0))
    side_income_duration = int(data.get('side_income_duration', 12))

    # --- Derived values ---
    annual_survival = (monthly_survival + dependent_cost) * 12
    annual_lifestyle = monthly_lifestyle * 12
    annual_total_expense = annual_survival + annual_lifestyle
    annual_passive = monthly_passive * 12

    total_assets = liquid_savings + semi_liquid + growth + prop
    emergency_lock = emergency_months * (monthly_survival + dependent_cost)

    # Inflation rates
    needs_inflation = 0.06
    wants_inflation = 0.07
    passive_growth = 0.04  # passive income grows slowly (rent revision etc.)
    property_appreciation = 0.05

    # --- Save assets to DB ---
    Asset.objects.filter(user=user).delete()

    current_year = datetime.now().year
    end_year = current_year + 20

    if liquid_savings > 0:
        Asset.objects.create(
            user=user, name='Liquid Savings', category='financial',
            start_year=current_year, end_year=end_year,
            initial_value=Decimal(str(liquid_savings)),
            return_pct=Decimal('6.0'), liquid=True,
            uncertainty_level='low',
        )
    if semi_liquid > 0:
        Asset.objects.create(
            user=user, name='Semi-Liquid (Debt MFs, Bonds, Gold)', category='financial',
            start_year=current_year, end_year=end_year,
            initial_value=Decimal(str(semi_liquid)),
            return_pct=Decimal('8.0'), liquid=False,
            uncertainty_level='low',
        )
    if growth > 0:
        Asset.objects.create(
            user=user, name='Growth (Equity, PF, NPS)', category='financial',
            start_year=current_year, end_year=end_year,
            initial_value=Decimal(str(growth)),
            return_pct=Decimal(str(data.get('expected_return', 12))),
            liquid=False, uncertainty_level='medium',
        )
    if prop > 0:
        Asset.objects.create(
            user=user, name='Property Equity', category='real_estate',
            start_year=current_year, end_year=end_year,
            initial_value=Decimal(str(prop)),
            appreciation_pct=Decimal('5.0'), return_pct=Decimal('3.0'),
            liquid=False, uncertainty_level='medium',
        )

    # --- Save expenses ---
    Expense.objects.filter(user=user).delete()

    Expense.objects.create(
        user=user, name='Survival Expenses', category='Living',
        budget_type='needs', start_year=current_year, end_year=end_year,
        typical_amount=Decimal(str(annual_survival)),
        inflation_pct=Decimal('6.0'), uncertainty_level='low',
    )
    if annual_lifestyle > 0:
        Expense.objects.create(
            user=user, name='Lifestyle Expenses', category='Discretionary',
            budget_type='wants', start_year=current_year, end_year=end_year,
            typical_amount=Decimal(str(annual_lifestyle)),
            inflation_pct=Decimal('7.0'), uncertainty_level='low',
        )

    for be in big_expenses:
        if be.get('name') and be.get('amount'):
            Expense.objects.create(
                user=user, name=be['name'], category='One-time',
                budget_type='needs', start_year=int(be.get('year', current_year + 5)),
                end_year=int(be.get('year', current_year + 5)),
                typical_amount=Decimal(str(be['amount'])),
                inflation_pct=Decimal('0'), uncertainty_level='medium',
            )

    # --- Save incomes ---
    Income.objects.filter(user=user).delete()

    if annual_passive > 0:
        Income.objects.create(
            user=user, name='Passive Income', category='others',
            start_year=current_year, end_year=end_year,
            typical_amount=Decimal(str(annual_passive)),
            growth_pct=Decimal('4.0'), uncertainty_level='low',
        )

    if has_side_income and side_income_amount > 0:
        side_end = current_year + max(1, side_income_duration // 12)
        Income.objects.create(
            user=user, name='Consulting / Side Income', category='salary',
            start_year=current_year, end_year=side_end,
            typical_amount=Decimal(str(side_income_amount * 12)),
            growth_pct=Decimal('0'), uncertainty_level='medium',
        )

    # --- Run projection ---
    years = list(range(current_year, end_year + 1))
    chart_needs = []
    chart_wants = []
    chart_incomes = []
    chart_assets = []

    # Mutable state
    cur_needs = annual_survival
    cur_wants = annual_lifestyle
    cur_passive = annual_passive
    cur_liquid = liquid_savings - emergency_lock
    cur_semi = semi_liquid
    cur_growth = growth
    cur_prop = prop
    free_up_year = None

    # Clear old projections
    CashflowProjection.objects.filter(user=user).delete()

    for i, year in enumerate(years):
        # --- Expenses for this year ---
        year_needs = cur_needs
        year_wants = cur_wants

        # Add big expenses hitting this year
        for be in big_expenses:
            if be.get('name') and be.get('amount') and int(be.get('year', 0)) == year:
                year_needs += float(be['amount'])

        year_total_expense = year_needs + year_wants

        # --- Income for this year ---
        year_passive = cur_passive

        # Side income
        year_side = 0
        if has_side_income and side_income_amount > 0:
            months_in = i * 12
            if months_in < side_income_duration:
                remaining = min(12, side_income_duration - months_in)
                year_side = side_income_amount * remaining

        # Asset returns (not liquidated — these are growth added to assets)
        semi_return = cur_semi * 0.08
        growth_return = cur_growth * expected_return_pct
        prop_return = cur_prop * 0.03  # rental yield on property

        year_total_income = year_passive + year_side + prop_return

        # --- Net cashflow ---
        net = year_total_income - year_total_expense

        # --- Asset values ---
        # Liquid covers shortfall first
        if net < 0:
            shortfall = abs(net)
            # Draw from liquid first, then semi, then growth
            if cur_liquid >= shortfall:
                cur_liquid -= shortfall
            elif cur_liquid + cur_semi >= shortfall:
                shortfall -= cur_liquid
                cur_liquid = 0
                cur_semi -= shortfall
            else:
                shortfall -= cur_liquid
                cur_liquid = 0
                shortfall -= cur_semi
                cur_semi = 0
                cur_growth = max(0, cur_growth - shortfall)
        else:
            # Surplus goes to growth assets
            cur_growth += net

        # Apply growth to assets
        cur_liquid *= 1.06  # savings account / liquid MF rate
        cur_semi += semi_return
        cur_growth += growth_return
        cur_prop *= (1 + 0.05)  # property appreciation

        total_assets_year = max(0, cur_liquid) + cur_semi + cur_growth + cur_prop

        # Check free-up: passive income from all assets >= expenses
        # Passive = 4% SWR on financial assets
        financial_assets = max(0, cur_liquid) + cur_semi + cur_growth
        potential_passive = financial_assets * 0.04 + cur_prop * 0.03
        if potential_passive >= year_total_expense and free_up_year is None and i > 0:
            free_up_year = year

        # Chart data (in lakhs for readability in chart)
        chart_needs.append(round(year_needs))
        chart_wants.append(round(year_wants))
        chart_incomes.append(round(year_total_income))
        chart_assets.append(round(total_assets_year))

        # Save projection row
        CashflowProjection.objects.create(
            user=user, year=year,
            total_income=Decimal(str(round(year_total_income, 2))),
            total_expense=Decimal(str(round(year_total_expense, 2))),
            expense_needs=Decimal(str(round(year_needs, 2))),
            expense_wants=Decimal(str(round(year_wants, 2))),
            net_cashflow=Decimal(str(round(net, 2))),
            total_assets=Decimal(str(round(total_assets_year, 2))),
            excess_cashflow=Decimal(str(round(max(0, net), 2))),
            shortfall=Decimal(str(round(abs(min(0, net)), 2))),
        )

        # Inflate for next year
        cur_needs *= (1 + needs_inflation)
        cur_wants *= (1 + wants_inflation)
        cur_passive *= (1 + passive_growth)

    return JsonResponse({
        'free_up_year': free_up_year,
        'chart_data': {
            'years': years,
            'needs': chart_needs,
            'wants': chart_wants,
            'incomes': chart_incomes,
            'assets': chart_assets,
        },
    })


# ============================================================================
# NEW SCENARIO-BASED API ENDPOINTS
# ============================================================================

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import ScenarioProfile
from .serializers import ScenarioProfileSerializer, QuestionSerializer
from .question_resolver import get_questions_for_scenario
from .calculators import get_calculator


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_scenario(request):
    """
    User selects their scenario type at app entry.
    Creates ScenarioProfile and returns initial questions.
    """
    scenario_type = request.data.get('scenario_type')

    if not scenario_type:
        return Response(
            {'error': 'scenario_type is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create or update scenario profile
    scenario, created = ScenarioProfile.objects.update_or_create(
        user=request.user,
        defaults={'scenario_type': scenario_type}
    )

    # Get or create family profile — ALWAYS reset to tier 1 on fresh scenario selection
    profile, _ = FamilyProfile.objects.get_or_create(
        user=request.user,
        defaults={'current_tier': 1}
    )
    profile.scenario = scenario
    profile.current_tier = 1  # Reset tier on new scenario
    profile.save()

    # Return initial questions for tier 1 (QUICK)
    tier_names = {1: 'QUICK', 2: 'STANDARD', 3: 'ADVANCED'}
    questions = get_questions_for_scenario(scenario_type, tier_names[profile.current_tier], skip_conditions=True)

    return Response({
        'scenario': ScenarioProfileSerializer(scenario).data,
        'current_tier': profile.current_tier,
        'tier_name': tier_names[profile.current_tier],
        'questions': [QuestionSerializer(q).to_representation(q) for q in questions],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_next_questions(request):
    """
    Returns next set of questions based on current tier and answers so far.
    Implements adaptive questioning logic.
    """
    try:
        scenario = ScenarioProfile.objects.get(user=request.user)
    except ScenarioProfile.DoesNotExist:
        return Response(
            {'error': 'No scenario selected. Call /api/scenarios/select/ first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    profile = FamilyProfile.objects.get(user=request.user)

    current_data = request.data.get('current_data', {})
    tier_names = {1: 'QUICK', 2: 'STANDARD', 3: 'ADVANCED'}

    questions = get_questions_for_scenario(
        scenario.scenario_type,
        tier_names[profile.current_tier],
        current_data,
        skip_conditions=True,  # Client handles conditional visibility
    )

    return Response({
        'questions': [QuestionSerializer(q).to_representation(q) for q in questions],
        'tier': profile.current_tier,
        'tier_name': tier_names[profile.current_tier],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compute_expenses_view(request):
    """
    Compute expense estimate from ExpenseMaster based on family composition.
    Called by frontend when expense_level is selected in tier 1.
    """
    from finance.services.expense_computer import compute_expenses

    data = request.data
    expense_level = data.get('expense_level')
    if not expense_level:
        return Response(
            {'error': 'expense_level is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = compute_expenses(
        expense_level=expense_level,
        family_type=data.get('family_type', 'solo'),
        kids_count=data.get('kids_count', 0),
        dependent_adults_count=data.get('dependent_adults_count', 0),
        has_vehicle=data.get('has_vehicle', False),
        has_pet=data.get('has_pet', False),
        rented_house=data.get('rented_house', False),
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_tier(request):
    """
    Runs calculation for current tier and returns results.
    #flow: calculate number comes here
    """
    try:
        scenario = ScenarioProfile.objects.get(user=request.user)
    except ScenarioProfile.DoesNotExist:
        return Response(
            {'error': 'No scenario selected. Call /api/scenarios/select/ first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    profile = FamilyProfile.objects.get(user=request.user)

    user_data = request.data.get('data')
    if not user_data:
        return Response(
            {'error': 'data field is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Apply any rate overrides submitted with this calculation, then inject
    from .models import UserRatePreferences
    rate_prefs, _ = UserRatePreferences.objects.get_or_create(user=request.user)

    submitted_rates = user_data.get('rates', {}) or {}
    if submitted_rates:
        RATE_FIELDS = {
            'liquid_return_pct', 'semi_liquid_return_pct', 'growth_return_pct',
            'property_appreciation_pct', 'property_rental_yield_pct',
            'needs_inflation_pct', 'wants_inflation_pct', 'passive_growth_pct', 'swr_rate_pct',
        }
        updated_fields = []
        for field in RATE_FIELDS:
            if field in submitted_rates and submitted_rates[field] is not None:
                setattr(rate_prefs, field, float(submitted_rates[field]))
                updated_fields.append(field)
        if updated_fields:
            rate_prefs.save(update_fields=updated_fields)

    user_data['rates'] = rate_prefs.as_dict()

    tier_names = {1: 'QUICK', 2: 'STANDARD', 3: 'ADVANCED'}
    current_tier_name = tier_names[profile.current_tier]

    # Get appropriate calculator
    try:
        calculator = get_calculator(
            scenario.scenario_type,
            current_tier_name,
            user_data
        )
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate required fields
    is_valid, missing_fields = calculator.validate_inputs()
    if not is_valid:
        return Response(
            {
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Run calculation
    try:
        results = calculator.calculate()
    except Exception as e:
        return Response(
            {'error': f'Calculation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Save assets to database for calculator logic
    # (Required by STANDARD tier calculators which model different asset classes)
    from datetime import datetime
    from decimal import Decimal

    Asset.objects.filter(user=request.user).delete()
    assets_data = user_data.get('assets', {})
    current_year = datetime.now().year
    end_year = current_year + 20

    if profile.current_tier == 1:  # QUICK tier
        living_total = float(assets_data.get('living_total', 0))
        security_total = float(assets_data.get('security_total', 0))

        # Default split for living assets: 60% liquid, 40% semi-liquid
        if living_total > 0:
            Asset.objects.create(
                user=request.user,
                name='Liquid Savings',
                category='financial',
                start_year=current_year,
                end_year=end_year,
                initial_value=Decimal(str(living_total * 0.6)),
                return_pct=Decimal('6.0'),
                liquid=True,
                uncertainty_level='low'
            )
            Asset.objects.create(
                user=request.user,
                name='Semi-Liquid (Bonds, Debt MFs)',
                category='financial',
                start_year=current_year,
                end_year=end_year,
                initial_value=Decimal(str(living_total * 0.4)),
                return_pct=Decimal('8.0'),
                liquid=False,
                uncertainty_level='low'
            )

        # Default split for security assets: 70% growth, 30% property
        if security_total > 0:
            Asset.objects.create(
                user=request.user,
                name='Growth (Equity, PF, NPS)',
                category='financial',
                start_year=current_year,
                end_year=end_year,
                initial_value=Decimal(str(security_total * 0.7)),
                return_pct=Decimal('12.0'),
                liquid=False,
                uncertainty_level='medium'
            )
            Asset.objects.create(
                user=request.user,
                name='Property',
                category='real_estate',
                start_year=current_year,
                end_year=end_year,
                initial_value=Decimal(str(security_total * 0.3)),
                appreciation_pct=Decimal('5.0'),
                return_pct=Decimal('3.0'),
                liquid=False,
                uncertainty_level='medium'
            )
    else:  # STANDARD tier or higher
        # Save exact breakdown provided by user
        asset_configs = {
            'liquid': {
                'name': 'Liquid Savings',
                'category': 'financial',
                'return_pct': Decimal('6.0'),
                'liquid': True,
                'uncertainty_level': 'low'
            },
            'semi_liquid': {
                'name': 'Semi-Liquid (Bonds, Debt MFs)',
                'category': 'financial',
                'return_pct': Decimal('8.0'),
                'liquid': False,
                'uncertainty_level': 'low'
            },
            'growth': {
                'name': 'Growth (Equity, PF, NPS)',
                'category': 'financial',
                'return_pct': Decimal('12.0'),
                'liquid': False,
                'uncertainty_level': 'medium'
            },
            'property': {
                'name': 'Property',
                'category': 'real_estate',
                'appreciation_pct': Decimal('5.0'),
                'return_pct': Decimal('3.0'),
                'liquid': False,
                'uncertainty_level': 'medium'
            }
        }

        for asset_type, value in assets_data.items():
            if value and float(value) > 0 and asset_type in asset_configs:
                config = asset_configs[asset_type]
                Asset.objects.create(
                    user=request.user,
                    name=config['name'],
                    category=config['category'],
                    start_year=current_year,
                    end_year=end_year,
                    initial_value=Decimal(str(value)),
                    appreciation_pct=config.get('appreciation_pct', Decimal('0')),
                    return_pct=config['return_pct'],
                    liquid=config['liquid'],
                    uncertainty_level=config['uncertainty_level']
                )

    return Response({
        'results': results,
        'tier': profile.current_tier,
        'tier_name': current_tier_name,
        'can_advance': profile.current_tier < 2,
        'username': request.user.username,
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def rate_preferences(request):
    """
    GET  — return current rate preferences (or defaults).
    PATCH — update one or more rate fields.
    """
    from .models import UserRatePreferences
    prefs, _ = UserRatePreferences.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        return Response({'rates': prefs.as_pct_dict()})

    # PATCH: update supplied fields
    ALLOWED = {
        'liquid_return_pct', 'semi_liquid_return_pct', 'growth_return_pct',
        'property_appreciation_pct', 'property_rental_yield_pct',
        'needs_inflation_pct', 'wants_inflation_pct',
        'passive_growth_pct', 'swr_rate_pct',
    }
    updated = []
    for field in ALLOWED:
        if field in request.data:
            setattr(prefs, field, request.data[field])
            updated.append(field)
    if updated:
        prefs.save(update_fields=updated)

    return Response({'rates': prefs.as_pct_dict(), 'updated': updated})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def advance_tier(request):
    """
    Advances user to next calculation tier.
    """
    profile = FamilyProfile.objects.get(user=request.user)

    if profile.current_tier < 3:
        profile.current_tier += 1
        profile.save()

        tier_names = {1: 'QUICK', 2: 'STANDARD', 3: 'ADVANCED'}

        return Response({
            'current_tier': profile.current_tier,
            'tier_name': tier_names[profile.current_tier],
            'message': f'Advanced to {tier_names[profile.current_tier]} tier'
        })
    else:
        return Response(
            {'error': 'Already at highest tier'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def advise(request):
    """
    Advanced tier: AI-powered financial advisor.
    Accepts the same user_data dict as calculate_tier plus the results
    from the most recent Standard calculation. Returns Asha's analysis.
    """
    from .advisor import get_advice

    user_data = request.data.get('data')
    results = request.data.get('results')

    if not user_data or not results:
        return Response(
            {'error': 'Both data and results fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if results.get('tier') != 'STANDARD':
        return Response(
            {'error': 'Advanced advisor requires Standard tier results. Complete the full projection first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Inject current rate preferences so Asha has accurate rates
    from .models import UserRatePreferences
    rate_prefs, _ = UserRatePreferences.objects.get_or_create(user=request.user)
    user_data['rates'] = rate_prefs.as_dict()

    try:
        advice_text = get_advice(user_data, results)
    except Exception as e:
        logger.exception('Advisor failed for user %s', request.user.id)
        return Response(
            {'error': f'Advisor unavailable: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return Response({'success': True, 'advice': advice_text})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def monte_carlo(request):
    """
    Advanced tier: Monte Carlo simulation over N paths (default 2,000).

    Accepts the same user_data dict as calculate_tier plus Standard tier
    results. Runs a vectorised NumPy simulation with perturbed annual returns,
    inflation, and random shock expenses.

    Returns fan chart data (P10/P25/P50/P75/P90) and success statistics.
    """
    from .calculators.monte_carlo import MonteCarloEngine

    user_data = request.data.get('data')
    results   = request.data.get('results')

    if not user_data or not results:
        return Response(
            {'error': 'Both data and results fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if results.get('tier') != 'STANDARD':
        return Response(
            {'error': 'Monte Carlo requires Standard tier results. Complete the full projection first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    scenario_type = results.get('scenario_type', '')
    if not scenario_type:
        return Response(
            {'error': 'scenario_type missing from results'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Inject current rate preferences so MC uses the same rates as the projection
    from .models import UserRatePreferences
    rate_prefs, _ = UserRatePreferences.objects.get_or_create(user=request.user)
    user_data['rates'] = rate_prefs.as_dict()

    try:
        engine     = MonteCarloEngine(user_data, scenario_type)
        mc_results = engine.run()
    except Exception as e:
        logger.exception('Monte Carlo failed for user %s', request.user.id)
        return Response(
            {'error': f'Simulation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({'success': True, 'mc': mc_results})
