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

# This file is used for setup.py test and setup.py testserver.

DEBUG = False
SITE_ID = 1
USE_I18N = False
ROOT_URLCONF = 'RestAuth.urls'
TEMPLATE_LOADERS = ()
TIME_ZONE = None  # None='same as os'
SECRET_KEY = 'dummy'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'RestAuth.common.middleware.RestAuthMiddleware',
)

CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'restauth'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testserver.sqlite3',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

ALLOWED_HOSTS = [
    '[::1]',
]

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

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'RestAuth.common.hashers.Sha512Hasher',
    'RestAuth.common.hashers.MediaWikiHasher',
    'RestAuth.common.hashers.Apr1Hasher',
    'RestAuth.common.hashers.Drupal7Hasher',
    'RestAuth.common.hashers.PhpassHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

CONTENT_HANDLERS = (
    'RestAuthCommon.handlers.JSONContentHandler',
    'RestAuthCommon.handlers.FormContentHandler',
    'RestAuthCommon.handlers.PickleContentHandler',
    'RestAuthCommon.handlers.YamlContentHandler',
)

# South settings:
SOUTH_TESTS_MIGRATE = False

#############################################
### Defaults for the standard settings.py ###
#############################################
RELAXED_LINUX_CHECKS = False
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 255
MIN_PASSWORD_LENGTH = 6
VALIDATORS = []
GROUP_RECURSION_DEPTH = 3
SECURE_CACHE = False
SERVICE_PASSWORD_HASHER = 'django.contrib.auth.hashers.MD5PasswordHasher'

# backends:
USER_BACKEND = 'RestAuth.backends.django_backend.DjangoUserBackend'
GROUP_BACKEND = 'RestAuth.backends.django_backend.DjangoGroupBackend'
PROPERTY_BACKEND = 'RestAuth.backends.django_backend.DjangoPropertyBackend'
#PROPERTY_BACKEND = 'RestAuth.backends.redis_backend.RedisPropertyBackend'
