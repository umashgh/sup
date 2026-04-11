import os
from django.contrib import admin
from django.urls import path, include
from django.views.defaults import page_not_found, server_error

# Non-guessable admin path — set ADMIN_URL env var in production.
# Default keeps /admin/ only in DEBUG mode so local dev still works.
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin')

urlpatterns = [
    path(f'{ADMIN_URL}/', admin.site.urls),
    path('accounts/', include('core.auth_urls')),
    path('forum/', include('forum.urls', namespace='forum')),
    path('', include('core.urls')),
    path('api/finance/', include('finance.urls')),
    path('api/ventures/', include('ventures.urls')),
]

# Custom minimal error pages — no Django branding, no stack traces
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
