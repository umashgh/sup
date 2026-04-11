from django.urls import path
from . import auth_views
from .encryption_views import (
    check_user_encryption, setup_encryption_view,
    remove_encryption_view, unlock_session_view,
)

urlpatterns = [
    path('login/',              auth_views.signin,            name='login'),
    path('logout/',             auth_views.signout,           name='logout'),
    path('signup/',             auth_views.signup,            name='signup'),
    path('check-username/',     auth_views.check_username,    name='check_username'),
    path('check-encryption/',   check_user_encryption,        name='check_user_encryption'),
    path('setup-encryption/',   setup_encryption_view,        name='setup_encryption'),
    path('remove-encryption/',  remove_encryption_view,       name='remove_encryption'),
    path('unlock-session/',     unlock_session_view,          name='unlock_session'),
]
