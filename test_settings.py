"""
Settings for testing the openedx_pok app.
"""

import warnings
from django.core.cache import CacheKeyWarning
from django.utils.crypto import get_random_string

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = get_random_string(50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'openedx_pok_test_db',
        'TEST': {
            'NAME': 'openedx_pok_test_db',
        }
    },
    'read_replica': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'openedx_pok_read_replica_db',
        'TEST': {
            'MIRROR': 'default',
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'default_loc_mem',
    },
}

ROOT_URLCONF = 'openedx_pok.urls'
SITE_ID = 1
USE_TZ = True

# Silence cache key warnings
warnings.simplefilter("ignore", CacheKeyWarning)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',  # Asegúrate de que esta línea esté presente
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    #'openedx.core.djangoapps.content.course_overviews',
    #'lms.djangoapps.courseware',

    'model_utils',      # Necesario por TimeStampedModel
    'openedx_pok',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

FEATURES = {
    'ENABLE_CSMH_EXTENDED': False,
}

TEST_APPS = ('openedx_pok',)
