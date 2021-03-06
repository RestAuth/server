# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not, see
# <http://www.gnu.org/licenses/>.

# This file is used for setup.py test and setup.py testserver.

import os

DEBUG = False
USE_I18N = False
ROOT_URLCONF = 'RestAuth.urls'
TEMPLATE_LOADERS = ()
TIME_ZONE = None  # None='same as os'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'common.middleware.RestAuthMiddleware',
]

CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'restauth'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    },
}
DATA_BACKEND = {
    'BACKEND': os.environ.get('DATA_BACKEND', 'backends.django.DjangoBackend'),
}

ALLOWED_HOSTS = [
    '[::1]',
]

INSTALLED_APPS = (
    # from django:
    'django.contrib.auth',
    'django.contrib.contenttypes',

    # our own apps:
    'Services',
    'Users',
    'Groups',
    'Test',
    'common',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.RemoteUserBackend',
    'Services.backend.InternalAuthenticationBackend',
)

PASSWORD_HASHERS = (
    #'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    #'common.hashers.Sha512Hasher',
    #'common.hashers.MediaWikiHasher',
    #'hashers_passlib.apr_md5_crypt',
    #'common.hashers.Drupal7Hasher',
    #'hashers_passlib.phpass',
    #'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    #'django.contrib.auth.hashers.BCryptPasswordHasher',
    #'django.contrib.auth.hashers.SHA1PasswordHasher',
    #'django.contrib.auth.hashers.MD5PasswordHasher',
    #'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
    #'django.contrib.auth.hashers.CryptPasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

CONTENT_HANDLERS = (
    'RestAuthCommon.handlers.JSONContentHandler',
    'RestAuthCommon.handlers.FormContentHandler',
    'RestAuthCommon.handlers.PickleContentHandler',
    'RestAuthCommon.handlers.YAMLContentHandler',
    'RestAuthCommon.handlers.BSONContentHandler',
    'RestAuthCommon.handlers.MessagePackContentHandler',
)

#########################################
# Defaults for the standard settings.py #
#########################################
RELAXED_LINUX_CHECKS = False
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 255
MIN_PASSWORD_LENGTH = 6
VALIDATORS = []
GROUP_RECURSION_DEPTH = 3
SECURE_CACHE = True
SERVICE_PASSWORD_HASHER = 'django.contrib.auth.hashers.MD5PasswordHasher'

# backends:
GROUP_BACKEND = 'backends.django.DjangoGroupBackend'
#GROUP_BACKEND = 'backends.memory_backend.MemoryGroupBackend'

LOG_HANDLER = 'logging.StreamHandler'
LOG_HANDLER_KWARGS = {}
LOG_LEVEL = 'ERROR'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s %(levelname)8s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'general': {
            'format': '%(levelname)s %(message)s',
        },
        'base': {
            'format': '%(levelname)s %(service)s: %(message)s',
        },
        'resource': {
            'format': '%(levelname)s %(service)s: %(name)s: %(message)s',
        },
        'subresource': {
            'format': '%(levelname)s %(service)s: %(name)s: %(subname)s: '
                      '%(message)s',
        },
    },
    'handlers': {
        'default': {
            'level': LOG_LEVEL,
            'class': LOG_HANDLER,
            'formatter': 'default',
        },
        'general': {
            'level': LOG_LEVEL,
            'class': LOG_HANDLER,
            'formatter': 'general',
        },
        'base': {
            'level': LOG_LEVEL,
            'class': LOG_HANDLER,
            'formatter': 'base',
        },
        'resource': {
            'level': LOG_LEVEL,
            'class': LOG_HANDLER,
            'formatter': 'resource',
        },
        'subresource': {
            'level': LOG_LEVEL,
            'class': LOG_HANDLER,
            'formatter': 'subresource',
        },
    },
    'loggers': {
        'RestAuth': {
            'handlers': ['default'],
            'propagate': False,
            'level': LOG_LEVEL,
        },
        'Services': {
            'handlers': ['default'],
            'propagate': False,
            'level': LOG_LEVEL,
        },
        'common': {
            'handlers': ['default'],
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
        },
    },
}
SECRET_KEY = 'dummy'
