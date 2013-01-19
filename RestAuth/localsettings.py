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


###################################
### RestAuth configuration file ###
###################################

# This file configures the behaviour of the RestAuth webservice. Please fill in
# the apropriate details below.

# Since the RestAuth service is implemented as a Django project, you can
# configure anything available in Django settings.py files. For more
# information on available settings and more thorough documentation on the
# settings given below, please see:
# 	http://docs.djangoproject.com/en/dev/ref/settings/

# Note: This file is imported from the real settings.py file, most settings are
#   already defined there. Given here are some settings that are typically of
#   interest for a system administrator, but you can always set any of the
#   other settings available in django, if you know what you are doing.

# Set debugging to "True" (without quotes) to get backtraces via HTTP. When set
# to False, backtraces will be sent to the adresses listed in the ADMINS
# variable.
# It is highly recommended to set DEBUG = False in any production environment.
#DEBUG = False

# Adresses that will receive backtraces when DEBUG=False
#ADMINS = (
#	('Your Name', 'your_email@domain.com'),
#)

# Configure your database settings
DATABASES = {
    'default': {
        # Use 'postgresql_psycopg2', 'postgresql', 'mysql' or 'oracle' instead
        # of 'sqlite3' to use a correct database backend:
        'ENGINE': 'django.db.backends.sqlite3',
        # Or path to database file if using sqlite3:
        'NAME': 'RestAuth.sqlite3',
        # Not used with sqlite3:
        'USER': '',
        # Not used with sqlite3:
        'PASSWORD': '',
        # Set to empty string for localhost. Not used with sqlite3:
        'HOST': '',
        # Set to empty string for default. Not used with sqlite3:
        'PORT': '',
    }
}

# You may want to configure a database router if you use some sort of database
# replication. For more information, please see:
#       https://server.restauth.net/config/database-replication.html
#DATABASE_ROUTERS = []

# Set your SECRET_KEY to some long random string:
SECRET_KEY = ''

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
#TIME_ZONE = 'Europe/Vienna'

#################
### USERNAMES ###
#################
# By default usernames can contain any UTF-8 character except for a colon
# (':'), a slash ('/') or a backslash ('\'). You can add validators to restrict
# usernames further to ensure compatibility with systems you use. For futher
# information please see:
#   https://server.restauth.net/config/username-validation.html
#
#VALIDATORS = [
#    'RestAuth.common.validators.xmpp',
#    'RestAuth.common.validators.mediawiki',
#]

# You can override the minimum and maximum username length. Note that this
# might be restricted even further if you add validators (see above).
#MIN_USERNAME_LENGTH = 3
#MAX_USERNAME_LENGTH = 255

#################
### PASSWORDS ###
#################
# You can configure various aspects on how RestAuth handles/stores passwords.
# All settings in this section are optional, the defaults are usually fine.

# Reconfigure the minimum password length. Only affects new passwords.
#MIN_PASSWORD_LENGTH = 6

# RestAuth uses Djangos default password hashing facilities. Please see:
#    https://docs.djangoproject.com/en/dev/topics/auth/passwords/
# for more information. RestAuth adds additional hashers for SHA-512, MediaWiki
# and Apr1 (Apache .htpasswd files). The default is:
#PASSWORD_HASHERS = (
#    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
#    'RestAuth.common.hashers.Sha512Hasher',
#    'RestAuth.common.hashers.MediaWikiHasher',
#    'RestAuth.common.hashers.Apr1Hasher',
#    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
#    'django.contrib.auth.hashers.BCryptPasswordHasher',
#    'django.contrib.auth.hashers.SHA1PasswordHasher',
#    'django.contrib.auth.hashers.MD5PasswordHasher',
#    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
#    'django.contrib.auth.hashers.CryptPasswordHasher',
#)


##############
### GROUPS ###
##############
# RestAuth supports nested groups where memberships of a group may be inherited
# from parent groups. You can configure how many levels of groups RestAuth
# checks. A recursion depth of 3 (=default) means that up to three levels of
# parent groups are checked.
#GROUP_RECURSION_DEPTH=3

################
### BACKENDS ###
################
# RestAuth can use different backends to store users, properties or groups.
# The backends can be configured individually, but some property/group backends
# may depend on a specific user backend. Please see:
#    https://server.restauth.net/developer/backends.html
# for more information.
#USER_BACKEND='RestAuth.backends.django_backend.DjangoUserBackend'
#GROUP_BACKEND='RestAuth.backends.django_backend.DjangoGroupBackend'
#PROPERTY_BACKEND='RestAuth.backends.django_backend.DjangoPropertyBackend'
PROPERTY_BACKEND='RestAuth.backends.redis_backend.RedisPropertyBackend'

###############
### CACHING ###
###############
# Django can use memcached to considerably speed up some requests. Note that
# due the Django caching implementation, the current performance improvement is
# not that great.  For more information on caching, please see:
# 	 https://docs.djangoproject.com/en/dev/topics/cache/

# Set your caching configuration here. Note that setting this will
# automatically enable the caching Middlewares as described in the Django
# documentation.
#CACHES = {}

###############
### LOGGING ###
###############
# Django has very powerful logging configuration capabilities. The full
# documentation can be found here:
#	 https://docs.djangoproject.com/en/dev/topics/logging/
# RestAuth uses a few settings that lets you have a good logging configuration
# with very few simple settings. If you want to, you can also define your very
# own logging config (see below). More information is also available in the
# settings reference:
#    https://restauth.net/config/all-config-values.html

# You can define the LogLevel for RestAuth. There are several possible values:
# * CRITICAL: Only log errors due to an internal malfunction.
# * ERROR:    Also log errors due to misbehaving clients.
# * WARNING:  Also log requests where an implicit assumption doesn't hold.
#	(i.e. when a client assumes that a user exists that in fact does not)
# * INFO:     Also log successfully processed requests that change data.
# * DEBUG:    Also log idempotent requests, i.e. if a user exists, etc.
#LOG_LEVEL = 'ERROR'

# You may also want to define a log handler and keyword arguments for it.
# Please see the python documentation on what this means:
# 	 http://docs.python.org/library/logging.config.html#configuration-dictionary-schema
# and possible handlers:
#	 http://docs.python.org/library/logging.handlers.html
#LOG_HANDLER = 'logging.StreamHandler'
#LOG_HANDLER_KWARGS = {}

# If you absolutely know what you are doing, you can simply set your own
# LOGGING config:
#LOGGING = { ... }

########################
### Session handling ###
########################
# HTTP sessions are disabled by default. You might want to set ENABLE_SESSIONS
# to True for libraries that require it. Note that this costs considerable
# performance.
#ENABLE_SESSIONS=False
