from django.contrib.auth.views import LogoutView
from django.urls import path
from . import auth_views

urlpatterns = [
    path('login/',  auth_views.signin, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', auth_views.signup, name='signup'),
]
