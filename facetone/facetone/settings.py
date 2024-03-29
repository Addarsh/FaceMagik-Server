"""
Django settings for facetone project.

Generated by 'django-admin startproject' using Django 3.0.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import psycopg2

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '^%@y3s!u$==f@#h8lvk81#xkkn&_1o(j73j30w%=@p5i(=*e@a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if 'RDS_DB_NAME' in os.environ:
    ALLOWED_HOSTS = [".elasticbeanstalk.com", ".awstrack.me", "34.215.220.1", "52.39.104.119", "52.42.104.250"]
else:
    ALLOWED_HOSTS = [".ngrok.io"]


# Application definition

INSTALLED_APPS = [
    'foundation.apps.FoundationConfig',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'facetone.urls'

AUTH_USER_MODEL = 'foundation.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'facetone.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
if 'RDS_DB_NAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
            'OPTIONS': {
                # Using Serializable which is the highest level of isolation offered by Postgres. Check out
                # https://www.youtube.com/watch?v=4EajrPgJAk0&t=1525s for an excellent explanation of different isolation
                # levels in Postgres with examples.
                'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE,
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'facemagik',
            'USER': 'django',
            'PASSWORD': 'django',
            'HOST': '127.0.0.1',
            'PORT': '5432',
            'OPTIONS': {
                # Using Serializable which is the highest level of isolation offered by Postgres. Check out
                # https://www.youtube.com/watch?v=4EajrPgJAk0&t=1525s for an excellent explanation of different isolation
                # levels in Postgres with examples.
                'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE,
            },
        }
    }


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Los_Angeles'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
