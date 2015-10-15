import os

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': 'test.db'
    }
}
MEDIA_ROOT = os.path.dirname(os.path.realpath(__file__))+'/tests',
ROOT_URLCONF = 'tests.urls',
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'etl_sync',
    'tests'
)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)
PROJECT_ROOT = os.path.join(
        *os.path.realpath(__file__).split('/')[0:-2])
SECRET_KEY = 'fake-key'

# Load machine specific setups (might be required to properly config spatialite)
try:
    from .test_settings_local import *
except ImportError:
    pass
