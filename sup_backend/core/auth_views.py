from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from finance.models import FamilyProfile

BACKEND = 'core.backends.UsernameOnlyBackend'


def signup(request):
    """
    Create account with just a username — no password.
    Transfers any in-progress guest session data to the new account.
    """
    error = None

    if request.user.is_authenticated and not request.user.username.startswith('guest_'):
        return redirect('scenario_selector')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        if not username:
            error = 'Please choose a username.'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif not username.replace('_', '').replace('-', '').isalnum():
            error = 'Only letters, numbers, hyphens and underscores are allowed.'
        elif User.objects.filter(username=username).exists():
            error = f'"{username}" is already taken — choose another.'
        else:
            guest_user = (
                request.user
                if request.user.is_authenticated and request.user.username.startswith('guest_')
                else None
            )

            new_user = User.objects.create_user(username=username)
            FamilyProfile.objects.get_or_create(user=new_user)

            if guest_user:
                _transfer_guest_data(guest_user, new_user)

            login(request, new_user, backend=BACKEND)
            next_url = request.POST.get('next') or request.GET.get('next') or _get_smart_redirect_for_user(new_user)
            if next_url.startswith('/'):
                return redirect(next_url)
            return redirect('scenario_selector')

    return render(request, 'registration/signup.html', {'error': error})


def signin(request):
    """
    Sign in with just a username — no password check.
    """
    error = None

    if request.user.is_authenticated and not request.user.username.startswith('guest_'):
        return redirect('scenario_selector')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if not username:
            error = 'Please enter your username.'
        else:
            user = authenticate(request, username=username)
            if user is None:
                return render(request, 'registration/login.html', {
                    'not_found': True,
                    'tried_username': username,
                })
            else:
                # Transfer any in-progress guest session to the signed-in account
                guest_user = (
                    request.user
                    if request.user.is_authenticated and request.user.username.startswith('guest_')
                    else None
                )
                if guest_user:
                    _transfer_guest_data(guest_user, user)

                login(request, user, backend=BACKEND)
                next_url = request.POST.get('next') or _get_smart_redirect_for_user(user)
                return redirect(next_url)

    return render(request, 'registration/login.html', {})


def signout(request):
    """Accept both POST and GET for mobile compatibility."""
    logout(request)
    return redirect('/')


def check_username(request):
    """Check if a username is available (for the suggest feature)."""
    username = request.GET.get('u', '').strip()
    if not username:
        return JsonResponse({'available': False})
    available = not User.objects.filter(username=username).exists()
    return JsonResponse({'available': available})


def _transfer_guest_data(guest_user, target_user):
    """Transfer in-progress guest scenario/profile data to the target user."""
    from core.models import ScenarioProfile
    # ScenarioProfile
    try:
        guest_sp = ScenarioProfile.objects.get(user=guest_user)
        existing_sp = ScenarioProfile.objects.filter(user=target_user).first()
        if existing_sp:
            existing_sp.scenario_type = guest_sp.scenario_type
            existing_sp.save()
            guest_sp.delete()
        else:
            guest_sp.user = target_user
            guest_sp.save()
    except ScenarioProfile.DoesNotExist:
        pass
    except Exception:
        pass
    # FamilyProfile
    try:
        guest_fp = FamilyProfile.objects.get(user=guest_user)
        target_fp, _ = FamilyProfile.objects.get_or_create(user=target_user)
        for field in ['current_tier', 'wealth_level', 'income_level',
                      'expense_level', 'monthly_expenses', 'emergency_fund_months']:
            val = getattr(guest_fp, field, None)
            if val is not None:
                setattr(target_fp, field, val)
        target_fp.save()
        guest_fp.delete()
    except Exception:
        pass
    try:
        guest_user.delete()
    except Exception:
        pass


def _get_smart_redirect_for_user(user):
    """Return the best redirect URL based on the user's saved progress."""
    try:
        from core.models import ScenarioProfile
        from finance.models import Asset
        ScenarioProfile.objects.get(user=user)
        fp = FamilyProfile.objects.get(user=user)
        if fp.current_tier >= 2:
            return '/results/'
        # Tier 1 calculation saves assets to DB — use that as completion signal
        if Asset.objects.filter(user=user).exists():
            return '/results/'
        return '/questions/'
    except Exception:
        return '/'
