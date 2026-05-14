def encryption_status(request):
    """Add encryption state and results availability to every template context."""
    has_enc = False
    data_unlocked = True
    user_has_results = False

    if request.user.is_authenticated and not request.user.username.startswith('guest_'):
        from core.models import UserEncryption, UserFlowState
        has_enc = UserEncryption.objects.filter(user=request.user).exists()
        data_unlocked = request.session.get('data_unlocked', not has_enc)
        try:
            fs = UserFlowState.objects.get(user=request.user)
            user_has_results = fs.tier1_results is not None
        except UserFlowState.DoesNotExist:
            pass

    return {
        'user_has_encryption': has_enc,
        'data_unlocked': data_unlocked,
        'user_has_results': user_has_results,
    }
