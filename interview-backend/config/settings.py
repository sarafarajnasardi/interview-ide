import os
from pathlib import Path
from urllib.parse import urlparse

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def get_bool_env(name, default=False):
    value = os.environ.get(name)

    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "on"}


def get_list_env(name, default=None):
    value = os.environ.get(name)

    if not value:
        return default or []

    return [item.strip() for item in value.split(",") if item.strip()]


def get_int_env(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def get_database_config():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }

    parsed_url = urlparse(database_url)

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed_url.path.lstrip("/"),
        "USER": parsed_url.username,
        "PASSWORD": parsed_url.password,
        "HOST": parsed_url.hostname,
        "PORT": parsed_url.port or 5432,
    }


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-2x=ok&%_i&_y5m55_o=@t)6-@_gi$x-nip(qfiz$7efuoory+^",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_bool_env("DJANGO_DEBUG", True)

ALLOWED_HOSTS = get_list_env("ALLOWED_HOSTS", ["*"])

render_external_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if render_external_hostname:
    ALLOWED_HOSTS.append(render_external_hostname)


# Application definition

INSTALLED_APPS = [
    "daphne",
    "channels",
    "corsheaders",
    "rest_framework",
    "submissions",
    
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
   
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": get_database_config(),
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

CORS_ALLOW_ALL_ORIGINS = get_bool_env("CORS_ALLOW_ALL_ORIGINS", True)
CORS_ALLOWED_ORIGINS = get_list_env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = get_list_env("CSRF_TRUSTED_ORIGINS")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = get_bool_env("DJANGO_SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = get_bool_env("DJANGO_SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = get_bool_env("DJANGO_CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = get_int_env("DJANGO_SECURE_HSTS_SECONDS", 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool_env("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = get_bool_env("DJANGO_SECURE_HSTS_PRELOAD", False)

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

INTERVIEW_ROOM_MAX_USERS = get_int_env("INTERVIEW_ROOM_MAX_USERS", 2)
INTERVIEW_ROOM_PRESENCE_TTL_SECONDS = get_int_env("INTERVIEW_ROOM_PRESENCE_TTL_SECONDS", 90)
