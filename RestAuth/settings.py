# This file is part of RestAuth (http://fs.fsinf.at/wiki/RestAuth).
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
#
###################################
### RestAuth configuration file ###
###################################

# This file configures the behaviour of the RestAuth webservice. Please fill in
# the apropriate details below.
#
# Since the RestAuth service is implemented as a Django project, you can
# configure anything available in Django settings.py files. For more information
# on available settings and more thorough documentation on the settings given
# below, please see:
# 	http://docs.djangoproject.com/en/dev/ref/settings/

# This import sets some sensible defaults that you usually don't want to
# override.
from djangosettings import *

# Set debugging to "True" (without quotes) to get backtraces via HTTP. When set
# to False, backtraces will be sent to the adresses listed in the ADMINS
# variable.
DEBUG = False

# Adresses that will receive backtraces when DEBUG=False
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# Configure your database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': './RestAuth.sqlite3', # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
#TIME_ZONE = 'Europe/Vienna'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
#LANGUAGE_CODE = 'en-us'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# A tricky problem for a shared authentication service is what characters are
# legal for a username. For example, 'Mathias Ertl' is a valid MediaWiki
# username, but it is not a valid XMPP username. When creating a new user, the
# username must pass tests for various systems. If the username is invalid in
# any of the systems, a user with that name cannot be created. RestAuth comes
# with a variety of validators, which essentially restrict the usernames to
# ASCII characters (a-z) and digits (0-9). For more information, please see:
# 	http://fs.fsinf.at/wiki/RestAuth/Usernames
#
# You can use this setting to disable some validators so you can support a wider
# range of usernames. Valid values are 'xmpp', 'email', 'mediawiki', 'linux' and
# 'windows'.
#SKIP_VALIDATORS = [ 'windows' ]

# Set to True if RestAuth should allow the username of a user to be changed:
#ALLOW_USERNAME_CHANGE = False

# You can override the minimum username and password length:
#MIN_USERNAME_LENGTH = 3

########################
### Session handling ###
########################
# HTTP sessions are disabled by default. You may want to enable it for libraries
# that require it. Note that this costs considerable performance.
#MIDDLEWARE_CLASSES.insert( 1,
#	'django.contrib.auth.middleware.AuthenticationMiddleware' )
#MIDDLEWARE_CLASSES.insert( 1,
#	'django.contrib.sessions.middleware.SessionMiddleware' )

###############
### CACHING ###
###############
# Django can use memcached to considerably speed up some requests. Note that due
# the Django caching implementation, the current performance improvement is not
# that great.

# If you want to use caching of any type, you must first uncomment these lines:
#MIDDLEWARE_CLASSES.insert( 0, 'django.middleware.cache.UpdateCacheMiddleware' )
#MIDDLEWARE_CLASSES.append( 'django.middleware.cache.FetchFromCacheMiddleware' )

# These are the required settings used by Django. See its documentation for
# detailed informations on these settings.
#CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
#CACHE_MIDDLEWARE_SECONDS = 300
#CACHE_MIDDLEWARE_KEY_PREFIX = ''

#################
### PASSWORDS ###
#################
# You can configure various aspects on how RestAuth handles/stores passwords.
# All settings in this section are optional, the defaults are usually fine.

# Reconfigure the minimum password length. Only affects new passwords.
#MIN_PASSWORD_LENGTH = 6

# Set a different hash algorithm for hashing passwords. This only affects newly
# created passwords, so you can safely change this at any time, old hashes will
# still work.
# 
# You can use the general algorithms, 'crypt', 'md5' and 'sha1'. 'sha1' is the
# default and recommended. Additionally, RestAuth supports using hashes
# compatible with other systems. Currectly 'mediawiki' creates hashes compatible
# with a MediaWiki database.
#HASH_ALGORITHM = 'sha512'

###############
### LOGGING ###
###############
# You can define the LogLevel for RestAuth. There are several possible values:
# * CRITICAL: Only log errors due to an internal malfunction.
# * ERROR:    Also log errors due to misbehaving clients.
# * WARNING:  Also log requests where an implicit assumption doesn't hold.
#	(i.e. when a client assumes that a user exists but in fact does not)
# * INFO:     Also log successfully processed requests that change data.
# * DEBUG:    Also log idempotent requests, i.e. if a user exists, etc.
#LOG_LEVEL = 'DEBUG'

# Define the target for logging. LOG_TARGET may either be 'stdout', 'stderr' or
# or a path to a filename. If RestAuth is run with mod_wsgi, 'stdout' does not 
# work and 'stderr' logs to the global apache log-file, not the VHOST log file.
#LOG_TARGET = 'stderr'
