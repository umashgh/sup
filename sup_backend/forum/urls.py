from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.forum_list, name='list'),
    path('new/', views.create_thread, name='create'),
    path('<int:pk>/', views.thread_detail, name='thread'),
    path('<int:pk>/reply/', views.add_reply, name='reply'),
    path('<int:pk>/react/', views.react, name='react'),
]
