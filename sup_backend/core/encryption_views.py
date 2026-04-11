import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core import encryption as enc
from core.models import UserEncryption


# ── API: check encryption status for a username (used on login page) ──────────

def check_user_encryption(request):
    """Return whether a given username has encryption set up."""
    username = request.GET.get('u', '').strip()
    if not username:
        return JsonResponse({'has_encryption': False, 'hint': None})
    try:
        user = User.objects.get(username=username)
        ue = UserEncryption.objects.get(user=user)
        return JsonResponse({'has_encryption': True, 'hint': ue.passphrase_hint or None})
    except (User.DoesNotExist, UserEncryption.DoesNotExist):
        return JsonResponse({'has_encryption': False, 'hint': None})


# ── API: set up encryption (for already-logged-in users) ─────────────────────

@login_required
@require_POST
def setup_encryption_view(request):
    try:
        body = json.loads(request.body)
    except (ValueError, TypeError):
        body = request.POST

    passphrase = (body.get('passphrase') or '').strip()
    hint = (body.get('hint') or '').strip()

    if len(passphrase) < 4:
        return JsonResponse({'success': False, 'error': 'Passphrase must be at least 4 characters.'})

    ue = enc.setup_encryption(request.user, passphrase, hint)
    # Store derived key in session so we can re-encrypt on logout
    key_b64 = enc.derive_key(passphrase, ue.kdf_salt).decode('utf-8')
    request.session['enc_key_b64'] = key_b64
    request.session['data_unlocked'] = True
    return JsonResponse({'success': True})


# ── API: unlock session (user is logged in but data is locked) ───────────────

@login_required
@require_POST
def unlock_session_view(request):
    """Decrypt and restore user data for the current session."""
    try:
        body = json.loads(request.body)
    except (ValueError, TypeError):
        body = request.POST

    passphrase = (body.get('passphrase') or '').strip()
    if not passphrase:
        return JsonResponse({'success': False, 'error': 'Passphrase required.'})

    try:
        ue = UserEncryption.objects.get(user=request.user)
    except UserEncryption.DoesNotExist:
        request.session['data_unlocked'] = True
        return JsonResponse({'success': True})

    ok = enc.unlock_and_restore(request.user, passphrase)
    if not ok:
        return JsonResponse({'success': False, 'error': 'Incorrect passphrase.'})

    key_b64 = enc.derive_key(passphrase, ue.kdf_salt).decode('utf-8')
    request.session['enc_key_b64'] = key_b64
    request.session['data_unlocked'] = True
    return JsonResponse({'success': True})


# ── API: remove encryption ───────────────────────────────────────────────────

@login_required
@require_POST
def remove_encryption_view(request):
    try:
        body = json.loads(request.body)
    except (ValueError, TypeError):
        body = request.POST

    passphrase = (body.get('passphrase') or '').strip()
    if not passphrase:
        return JsonResponse({'success': False, 'error': 'Passphrase required.'})

    ok = enc.remove_encryption(request.user, passphrase)
    if not ok:
        return JsonResponse({'success': False, 'error': 'Incorrect passphrase.'})

    request.session.pop('enc_key_b64', None)
    request.session['data_unlocked'] = True
    return JsonResponse({'success': True})
