def encryption_status(request):
    """Add encryption state to every template context."""
    has_enc = False
    data_unlocked = True

    if request.user.is_authenticated and not request.user.username.startswith('guest_'):
        from core.models import UserEncryption
        has_enc = UserEncryption.objects.filter(user=request.user).exists()
        data_unlocked = request.session.get('data_unlocked', not has_enc)

    return {
        'user_has_encryption': has_enc,
        'data_unlocked': data_unlocked,
    }
