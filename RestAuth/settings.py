# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RestAuth.  If not, see <http://www.gnu.org/licenses/>.


###############################
### Default Django settings ###
###############################
# These settings are set for Django, a sysadmin will rarely need to change
# these.

# Set debugging to "True" (without quotes) to get backtraces via HTTP. When set
# to False, backtraces will be sent to the adresses listed in the ADMINS
# variable.
# It is highly recommended to set DEBUG = False in any production environment.
DEBUG = False
SITE_ID = 1
USE_I18N = False
ROOT_URLCONF = 'RestAuth.urls'
TEMPLATE_LOADERS = ()
TIME_ZONE = None  # None='same as os'

# do not insert session middleware:
ENABLE_SESSIONS = False
CACHES = {}
LOGGING = {}
LOG_HANDLER = 'logging.StreamHandler'
LOG_HANDLER_KWARGS = {}
LOG_LEVEL = 'ERROR'

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'RestAuth.common.middleware.ExceptionMiddleware',
    'RestAuth.common.middleware.HeaderMiddleware',
]

CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'restauth'

INSTALLED_APPS = (
    # from django:
    'django.contrib.auth',
    'django.contrib.contenttypes',

    # schema migrations:
    'south',

    # our own apps:
    'RestAuth.Services',
    'RestAuth.Users',
    'RestAuth.Groups',
    'RestAuth.Test',
    'RestAuth.common',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.RemoteUserBackend',
    'RestAuth.Services.backend.InternalAuthenticationBackend',
)

#############################################
### Defaults for the standard settings.py ###
#############################################
RELAXED_LINUX_CHECKS = False
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 255
MIN_PASSWORD_LENGTH = 6
HASH_ALGORITHM = 'sha512'
HASH_FUNCTIONS = [
    'RestAuth.Users.hashes.mediawiki',
    'RestAuth.Users.hashes.crypt',
    'RestAuth.Users.hashes.apr1',
]
VALIDATORS = []

try:
    from localsettings import *
except ImportError:
    pass

if not LOGGING:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'general': {
                'format': '%(levelname)s %(message)s'
            },
            'base': {
                'format': '%(levelname)s %(service)s: %(message)s'
            },
            'resource': {
                'format': '%(levelname)s %(service)s: %(name)s: %(message)s'
            },
            'subresource': {
                'format': '%(levelname)s %(service)s: %(name)s: %(subname)s: '
                          '%(message)s'
            },
        },
        'handlers': {
            'general': {
                'level': LOG_LEVEL,
                'class': LOG_HANDLER,
                'formatter': 'general'
            },
            'base': {
                'level': LOG_LEVEL,
                'class': LOG_HANDLER,
                'formatter': 'base'
            },
            'resource': {
                'level': LOG_LEVEL,
                'class': LOG_HANDLER,
                'formatter': 'resource'
            },
            'subresource': {
                'level': LOG_LEVEL,
                'class': LOG_HANDLER,
                'formatter': 'subresource'
            },
        },
        'loggers': {
            'general': {
                'handlers': ['general'],
                'propagate': False,
                'level': LOG_LEVEL,
            },
            'users': {
                'handlers': ['base'],
                'propagate': False,
                'level': LOG_LEVEL,
            },
            'users.user': {
                'handlers': ['resource'],
                'propagate': False,
                'level': LOG_LEVEL,
            },
            'users.user.props': {
                'handlers': ['resource'],
                'propagate': False,
                'level': LOG_LEVEL,
            },
            'users.user.props.prop': {
                'handlers': ['subresource'],
                'propagate': False,
                'level': LOG_LEVEL,
            },
            'groups': {
                'handlers': ['base'],
                'propagate': False,
                'level': LOG_LEVEL,
            },
            'groups.group': {
                'handlers': ['resource'],
                'propagate': False,
                'level': LOG_LEVEL,
            },
            'groups.group.users': {
                'handlers': ['resource'],
                'propagate': False,
                'level': LOG_LEVEL,
            },
            'groups.group.users.user': {
                'handlers': ['subresource'],
                'propagate': False,
                'level': LOG_LEVEL,
            },
            'groups.group.groups': {
                'handlers': ['resource'],
                'propagate': False,
            'level': LOG_LEVEL,
            },
            'groups.group.groups.subgroup': {
                'handlers': ['subresource'],
                'propagate': False,
                'level': LOG_LEVEL,
            }
        }
    }

    if LOG_HANDLER_KWARGS:
        for handler in LOGGING['handlers'].values():
            handler.update(LOG_HANDLER_KWARGS)

if ENABLE_SESSIONS:
    index = MIDDLEWARE_CLASSES.index(
        'django.middleware.common.CommonMiddleware') + 1
    MIDDLEWARE_CLASSES.insert(
        index,
        'django.contrib.auth.middleware.AuthenticationMiddleware'
    )
    MIDDLEWARE_CLASSES.insert(
        index,
        'django.contrib.sessions.middleware.SessionMiddleware'
    )

if CACHES:
    MIDDLEWARE_CLASSES.insert(
        0, 'django.middleware.cache.UpdateCacheMiddleware')
    MIDDLEWARE_CLASSES.append(
        'django.middleware.cache.FetchFromCacheMiddleware')
SOUTH_TESTS_MIGRATE = False
