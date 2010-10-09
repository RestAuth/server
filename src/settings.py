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

# This import sets some sensible defaults, that you usually don't want to
# override.
import djangosettings 

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
TIME_ZONE = 'Europe/Vienna'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# Use this setting to configure how RestAuth assumes service authentication
# is performed:
# * internal: HTTP basic authentication is evaluated by RestAuth itself.
# * apache: RestAuth trusts the HTTP headers passed on to it by the webserver.
# The latter setting is faster but requires more configuration. For more
# information, please see:
# 	http://fs.fsinf.at/wiki/RestAuth/Service_authentication
RESTAUTH_AUTH_PROVIDER = 'internal'

# A tricky problem for a shared authentication service is what characters are
# legal for a username. For example, 'Mathias Ertl' is a valid MediaWiki
# username, but it is not valid XMPP username. When creating a new user, the
# username must pass tests for various systems. If the username is invalid in
# any of the systems, a user with that name cannot be created. RestAuth comes
# with a variety of validators, which essentially restrict the usernames to
# ASCII characters (a-z) and digits (0-9). For more information, please see:
# 	http://fs.fsinf.at/wiki/RestAuth/Usernames
#
# You can use this setting to disable some validators so you can support a wider
# range of usernames. Valud values are 'xmpp', 'email', 'mediawiki', 'linux' and
# 'windows'.
SKIP_VALIDATORS = [ 'windows' ]
