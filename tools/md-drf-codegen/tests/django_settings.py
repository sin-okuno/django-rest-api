"""Minimal Django settings for generator tests."""

SECRET_KEY = "test-secret-key"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
]
ROOT_URLCONF = "tests.urls"
USE_TZ = True
