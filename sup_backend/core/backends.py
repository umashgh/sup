from django.contrib.auth.models import User


class UsernameOnlyBackend:
    """
    Authenticate by username alone — no password.
    Used for the "save your progress" account model where the user
    picks a handle and we persist their data under it.
    """

    def authenticate(self, request, username=None):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
