"""
Django settings for Healthcare AI & Machine Learning Management Web Application.
Operates 100% locally with zero external APIs and zero relational/document database engines.
All persistence uses local JSON and CSV files.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-healthcare-ai-ml-local-storage-system-key-2026-secure'

# SECURITY WARNING: don't run with debug turned off in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.sessions',
    # Custom apps
    'core',
    'accounts',
    'patients',
    'doctors',
    'health',
    'appointments',
    'ml',
    'nlp',
    'recommendations',
    'notifications',
    'analytics',
    'admin_panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom auth middleware for JSON user session binding
    'accounts.middleware.JsonAuthMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.auth_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database configuration: Strictly NO database used as per project requirements
DATABASES = {}

# Session engine: Signed cookies (no database table required)
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_NAME = 'healthcare_sessionid'
SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Password validation & security
PASSWORD_HASH_ALGORITHM = 'pbkdf2_sha256'
PASSWORD_HASH_ITERATIONS = 100000

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Data Directory for JSON & CSV Storage
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

# ML Models Directory
ML_MODELS_DIR = BASE_DIR / 'ml' / 'models'
ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ML Datasets Directory
ML_DATASETS_DIR = BASE_DIR / 'ml' / 'datasets'
ML_DATASETS_DIR.mkdir(parents=True, exist_ok=True)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom File-based Storage Paths
JSON_FILES = {
    'users': DATA_DIR / 'users.json',
    'patients': DATA_DIR / 'patients.json',
    'doctors': DATA_DIR / 'doctors.json',
    'health_profiles': DATA_DIR / 'health_profiles.json',
    'medical_history': DATA_DIR / 'medical_history.json',
    'symptoms': DATA_DIR / 'symptoms.json',
    'appointments': DATA_DIR / 'appointments.json',
    'predictions': DATA_DIR / 'predictions.json',
    'recommendations': DATA_DIR / 'recommendations.json',
    'notifications': DATA_DIR / 'notifications.json',
    'audit_logs': DATA_DIR / 'audit_logs.json',
}
