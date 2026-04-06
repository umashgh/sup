from django.urls import path
from . import auth_views

urlpatterns = [
    path('login/',          auth_views.signin,         name='login'),
    path('logout/',         auth_views.signout,        name='logout'),
    path('signup/',         auth_views.signup,         name='signup'),
    path('check-username/', auth_views.check_username, name='check_username'),
]
