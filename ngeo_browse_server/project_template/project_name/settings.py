#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 European Space Agency
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

"""
Django settings for ngEO Browse Server's {{ project_name }} instance.

"""
from os.path import join

PROJECT_DIR = '{{ project_directory }}/{{ project_name }}'
PROJECT_URL_PREFIX = ''

#TEST_RUNNER = 'eoxserver.testing.core.EOxServerTestRunner'

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('EOX', 'office@eox.at'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',                  # Use 'spatialite' or change to 'postgis'.
        'NAME': '{{ project_directory }}/{{ project_name }}/data/data.sqlite',  # Or path to database file if using spatialite.
        #'TEST_NAME': '{{ project_directory }}/{{ project_name }}/data/test-data.sqlite', # Required for certain test cases, but slower!
        'USER': '',                                                             # Not used with spatialite.
        'PASSWORD': '',                                                         # Not used with spatialite.
        'HOST': '',                                                             # Set to empty string for localhost. Not used with spatialite.
        'PORT': '',                                                             # Set to empty string for default. Not used with spatialite.
    },
    'mapcache': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '{{ project_directory }}/{{ project_name }}/data/mapcache.sqlite',
        #'TEST_NAME': '{{ project_directory }}/{{ project_name }}/data/test-mapcache.sqlite',
    }
}

DATABASE_ROUTERS = ['ngeo_browse_server.dbrouters.MapCacheRouter', ]

# Use faster ramfs tablespace for testing for PostGIS e.g. in Jenkins
# Configure via:
#    mount -t ramfs none /mnt/
#    mkdir /mnt/pgdata/
#    chown postgres:postgres /mnt/pgdata/
#    su postgres
#    psql -d postgres -c "CREATE TABLESPACE ramfs LOCATION '/mnt/pgdata'"
#    psql -d postgres -c "GRANT CREATE ON TABLESPACE ramfs TO jenkins;"
#    exit
#from sys import argv
#if 'test' in argv:
#    DEFAULT_TABLESPACE = 'ramfs'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
# Note that this is the time zone to which Django will convert all
# dates/times -- not necessarily the timezone of the server.
# If you are using UTC (Zulu) time zone for your data (e.g. most
# satellite imagery) it is highly recommended to use 'UTC' here. Otherwise
# you will encounter time-shifts between your data, search request & the
# returned results.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = join(PROJECT_DIR, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '{{ secret_key }}'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
# Commented because of POST requests:    'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'ngeo_browse_server.storage.middleware.AuthTokenMiddleware'
)

ROOT_URLCONF = '{{ project_name }}.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = '{{ project_name }}.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    join(PROJECT_DIR, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.gis',
    'django.contrib.staticfiles',
    # Enable the admin:
    'django.contrib.admin',
    # Enable admin documentation:
    'django.contrib.admindocs',
#    'django.contrib.databrowse',
#    'django_extensions',
    # Enable EOxServer:
    'eoxserver.core',
    'eoxserver.services',
    'eoxserver.resources.coverages',
    'eoxserver.resources.processes',
    'eoxserver.backends',
    'eoxserver.testing',
    'eoxserver.webclient',
    # Enable ngEO Browse Server:
    'ngeo_browse_server.config',
    'ngeo_browse_server.control',
    'ngeo_browse_server.mapcache',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'simple': {
            'format': '%(levelname)s: %(message)s'
        },
        'verbose': {
            'format': '[%(asctime)s][%(module)s] %(levelname)s: %(message)s'
        },
        'ingest': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'eoxserver_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': join(PROJECT_DIR, 'logs', 'eoxserver.log'),
            'formatter': 'verbose' if DEBUG else 'simple',
            'filters': [],
        },
        'ngeo_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': join(PROJECT_DIR, 'logs', 'ngeo.log'),
            'formatter': 'verbose' if DEBUG else 'simple',
            'filters': [],
        },
        'controller_server_notification': {
            'level': 'WARNING',
            'class': 'ngeo_browse_server.control.control.notification.NotifyControllerServerHandler',
        },
        'ngEO-ingest': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': join(PROJECT_DIR, 'logs', 'ingest.log'),
            'formatter': 'ingest',
            'filters': [],
        }
    },
    'loggers': {
        'eoxserver': {
            'handlers': ['eoxserver_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'ngeo_browse_server': {
            'handlers': ['ngeo_file', 'controller_server_notification'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        # for ingest reports
        'ngEO-ingest': {
            'handlers': ['ngEO-ingest'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

FIXTURE_DIRS = (
    join(PROJECT_DIR, 'data/fixtures'),
)

# Set this variable if the path to the instance cannot be resolved
# automatically, e.g. in case of redirects
#FORCE_SCRIPT_NAME="/path/to/instance/"
