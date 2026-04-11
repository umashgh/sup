from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from finance.models import FamilyProfile
from core.models import UserEncryption

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
    If the user has encryption set up, an optional passphrase can be submitted
    to decrypt and restore their data for the session.
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

                # Handle encryption unlock / removal before completing login
                passphrase = request.POST.get('passphrase', '').strip()
                remove_enc = request.POST.get('remove_encryption') == '1'
                try:
                    ue = UserEncryption.objects.get(user=user)
                    if passphrase and remove_enc:
                        from core import encryption as enc
                        ok = enc.remove_encryption(user, passphrase)
                        if not ok:
                            return render(request, 'registration/login.html', {
                                'passphrase_error': 'Incorrect passphrase. Encryption not removed.',
                                'username_prefill': username,
                                'has_encryption': True,
                                'passphrase_hint': ue.passphrase_hint or None,
                            })
                        login(request, user, backend=BACKEND)
                        request.session['data_unlocked'] = True
                        next_url = request.POST.get('next') or _get_smart_redirect_for_user(user)
                        return redirect(next_url)
                    elif passphrase:
                        from core import encryption as enc
                        ok = enc.unlock_and_restore(user, passphrase)
                        if not ok:
                            return render(request, 'registration/login.html', {
                                'passphrase_error': 'Incorrect passphrase. Your data remains encrypted.',
                                'username_prefill': username,
                                'has_encryption': True,
                                'passphrase_hint': ue.passphrase_hint or None,
                            })
                        login(request, user, backend=BACKEND)
                        key_b64 = enc.derive_key(passphrase, ue.kdf_salt).decode('utf-8')
                        request.session['enc_key_b64'] = key_b64
                        request.session['data_unlocked'] = True
                        next_url = request.POST.get('next') or _get_smart_redirect_for_user(user)
                        return redirect(next_url)
                    else:
                        login(request, user, backend=BACKEND)
                        request.session['data_unlocked'] = False
                except UserEncryption.DoesNotExist:
                    login(request, user, backend=BACKEND)
                    request.session['data_unlocked'] = True

                next_url = request.POST.get('next') or _get_smart_redirect_for_user(user)
                return redirect(next_url)

    # GET — check if we should pre-show encryption UI based on username in query params
    prefill_username = request.GET.get('u', '')
    ctx = {'username_prefill': prefill_username}
    if prefill_username:
        try:
            u = User.objects.get(username=prefill_username)
            ue = UserEncryption.objects.get(user=u)
            ctx['has_encryption'] = True
            ctx['passphrase_hint'] = ue.passphrase_hint or None
        except (User.DoesNotExist, UserEncryption.DoesNotExist):
            pass
    return render(request, 'registration/login.html', ctx)


def signout(request):
    """Accept both POST and GET for mobile compatibility.
    Re-encrypts user data before clearing the session if encryption is active."""
    enc_key = request.session.get('enc_key_b64')
    user = request.user
    if enc_key and user.is_authenticated and not user.username.startswith('guest_'):
        try:
            from core import encryption as enc_module
            enc_module.reencrypt_user_data(user, enc_key)
        except Exception:
            pass  # Never block logout on encryption errors
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
