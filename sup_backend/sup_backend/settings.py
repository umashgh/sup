"""
Django settings for sup_backend project.
"""

import os
from pathlib import Path
import dotenv
import socket

dotenv.load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Core secrets — read from environment; never hardcode in source
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-only-change-in-production')

# Debug defaults to True locally so developers don't need to set env vars.
# Production deploy MUST set DEBUG=False in the environment.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,salaryfree.in,www.salaryfree.in'
).split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://salaryfree.in',
    'https://www.salaryfree.in',
]

try:
    fqdn = socket.getfqdn()
    ALLOWED_HOSTS.append(fqdn)
    CSRF_TRUSTED_ORIGINS.append(f'https://{fqdn}')
    print(CSRF_TRUSTED_ORIGINS)
except:
    pass

# ---------------------------------------------------------------------------
# Security headers (safe to set unconditionally; SSL redirect gated on DEBUG)
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Only redirect to HTTPS and send HSTS in production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000          # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False  # must be False so JS can read csrftoken for fetch() calls

X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True           # legacy IE header, harmless on modern browsers
SECURE_REFERRER_POLICY = 'same-origin'

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_htmx',
    'django_bootstrap5',
    'rest_framework',
    'rest_framework.authtoken',
    'axes',
    'finance',
    'ventures',
    'core',
    'forum',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # axes must come after AuthenticationMiddleware
    'axes.middleware.AxesMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'sup_backend.middleware.ContentSecurityPolicyMiddleware',
]

ROOT_URLCONF = 'sup_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.encryption_status',
            ],
        },
    },
]

WSGI_APPLICATION = 'sup_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = [
    # axes must be first so it can block before the real auth runs
    'axes.backends.AxesStandaloneBackend',
    'core.backends.UsernameOnlyBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ---------------------------------------------------------------------------
# django-axes — brute-force login protection
# Lock out an IP after 5 failed attempts within 15 minutes.
# ---------------------------------------------------------------------------
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 0.25           # hours (= 15 minutes)
AXES_LOCKOUT_PARAMETERS = ['ip_address']
AXES_RESET_ON_SUCCESS = True       # clear failure count on successful login
AXES_LOCKOUT_CALLABLE = 'core.views.axes_lockout_response'

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
_TELEGRAM_TOKEN   = os.environ.get('TELEGRAM_BOT_TOKEN', '')
_TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'telegram': {
            'class': 'sup_backend.telegram_log_handler.TelegramHandler',
            'level': 'ERROR',
            'formatter': 'simple',
            'token':   _TELEGRAM_TOKEN,
            'chat_id': _TELEGRAM_CHAT_ID,
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'telegram'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'telegram'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
}
