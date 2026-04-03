from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_POST
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

            # Transfer guest session data to the new account
            if guest_user:
                try:
                    from core.models import ScenarioProfile
                    sp = ScenarioProfile.objects.get(user=guest_user)
                    sp.user = new_user
                    sp.save()
                except Exception:
                    pass
                try:
                    guest_fp = FamilyProfile.objects.get(user=guest_user)
                    new_fp, _ = FamilyProfile.objects.get_or_create(user=new_user)
                    for field in ['current_tier', 'wealth_level', 'income_level',
                                  'expense_level', 'monthly_expenses', 'emergency_fund_months']:
                        val = getattr(guest_fp, field, None)
                        if val is not None:
                            setattr(new_fp, field, val)
                    new_fp.save()
                    guest_fp.delete()
                except Exception:
                    pass
                try:
                    guest_user.delete()
                except Exception:
                    pass

            login(request, new_user, backend=BACKEND)
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
                error = f'No account found for "{username}".'
            else:
                login(request, user, backend=BACKEND)
                return redirect(request.POST.get('next') or '/')

    return render(request, 'registration/login.html', {'error': error})


@require_POST
def signout(request):
    logout(request)
    return redirect('/')
