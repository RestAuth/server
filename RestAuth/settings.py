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
TIME_ZONE=None  #None='same as os'

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
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'RestAuth.Services',
	'RestAuth.Users',
	'RestAuth.Groups',
        'RestAuth.Test',
)

AUTHENTICATION_BACKENDS = (
	'django.contrib.auth.backends.RemoteUserBackend',
	'RestAuth.Services.backend.InternalAuthenticationBackend',
)

#############################################
### Defaults for the standard settings.py ###
#############################################
SKIP_VALIDATORS = [ 'linux', 'windows', 'email', 'xmpp' ]
FILTER_LINUX_USERNAME_NOT_RECOMMENDED = True
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 255
MIN_PASSWORD_LENGTH = 6
HASH_ALGORITHM = 'sha512'


try:
	from localsettings import *
except ImportError:
	pass

if not LOGGING:
	LOGGING = {
		'version': 1,
		'disable_existing_loggers': True,
		'formatters': {
			'users': {
				'format': '%(levelname)s %(service)s: %(message)s'
			},
			'users.user': { 
				'format': '%(levelname)s %(service)s: %(username)s: %(message)s'
			},
			'users.user.props.prop': { 
				'format': '%(levelname)s %(service)s: %(username)s: %(prop)s: %(message)s'
			},
			'groups': {
				'format': '%(levelname)s %(service)s: %(message)s'
			},
			'groups.group' : {
				'format': '%(levelname)s %(service)s: %(group)s: %(message)s'
			},
			'groups.group.users' : {
				'format': '%(levelname)s %(service)s: %(group)s: %(message)s'
			},
			'groups.group.users.user' : {
				'format': '%(levelname)s %(service)s: %(group)s: %(user)s: %(message)s'
			},
			'groups.group.groups' : {
				'format': '%(levelname)s %(service)s: %(group)s: %(message)s'
			},
			'groups.group.groups.subgroup' : {
				'format': '%(levelname)s %(service)s: %(group)s: %(subgroup)s: %(message)s'
			},
		},
		'handlers': {
			'users':{
				'level': LOG_LEVEL,
				'class': LOG_HANDLER,
				'formatter': 'users'
			},
			'users.user':{
				'level': LOG_LEVEL,
				'class': LOG_HANDLER,
				'formatter': 'users.user'
			},
			'users.user.props.prop':{
				'level': LOG_LEVEL,
				'class': LOG_HANDLER,
				'formatter': 'users.user.props.prop'
			},
			'groups':{
				'level': LOG_LEVEL,
				'class': LOG_HANDLER,
				'formatter': 'groups'
			},
			'groups.group': {
				'level': LOG_LEVEL,
				'class': LOG_HANDLER,
				'formatter': 'groups.group'
			},
			'groups.group.users': {
				'level': LOG_LEVEL,
				'class': LOG_HANDLER,
				'formatter': 'groups.group.users'
			},
			'groups.group.users.user': {
				'level': LOG_LEVEL,
				'class': LOG_HANDLER,
				'formatter': 'groups.group.users.user'
			},
			'groups.group.groups': {
				'level': LOG_LEVEL,
				'class': LOG_HANDLER,
				'formatter': 'groups.group.groups'
			},
			'groups.group.groups.subgroup': {
				'level': LOG_LEVEL,
				'class': LOG_HANDLER,
				'formatter': 'groups.group.groups.subgroup'
			}
		},
		'loggers': {
			'users': {
				'handlers':['users'],
				'propagate': False,
				'level': LOG_LEVEL,
			},
			'users.user': {
				'handlers':['users.user'],
				'propagate': False,
				'level': LOG_LEVEL,
			},
			'users.user.props': { # we have no additional info here!
				'handlers':['users.user'],
				'propagate': False,
				'level': LOG_LEVEL,
			},
			'users.user.props.prop': {
				'handlers':['users.user.props.prop'],
				'propagate': False,
				'level': LOG_LEVEL,
			},
			'groups': {
				'handlers':['groups'],
				'propagate': False,
				'level': LOG_LEVEL,
			},
			'groups.group': {
				'handlers':['groups.group'],
				'propagate': False,
				'level': LOG_LEVEL,
			},
			'groups.group.users': {
				'handlers':['groups.group.users'],
				'propagate': False,
				'level': LOG_LEVEL,
			},
			'groups.group.users.user': {
				'handlers':['groups.group.users.user'],
				'propagate': False,
				'level': LOG_LEVEL,
			},
			'groups.group.groups': {
				'handlers':['groups.group.groups'],
				'propagate': False,
			'level': LOG_LEVEL,
			},
			'groups.group.groups.subgroup': {
				'handlers':['groups.group.groups.subgroup'],
				'propagate': False,
				'level': LOG_LEVEL,
			}
		}
	}
	
	if LOG_HANDLER_KWARGS:
		for handler in LOGGING['handlers'].values():
			handler.update( LOG_HANDLER_KWARGS )
	
if ENABLE_SESSIONS:
	index = MIDDLEWARE_CLASSES.index( 'django.middleware.common.CommonMiddleware' ) + 1
	MIDDLEWARE_CLASSES.insert( index,
		'django.contrib.auth.middleware.AuthenticationMiddleware' )
	MIDDLEWARE_CLASSES.insert( index,
		'django.contrib.sessions.middleware.SessionMiddleware' )

if CACHES:
	MIDDLEWARE_CLASSES.insert( 0, 'django.middleware.cache.UpdateCacheMiddleware' )
	MIDDLEWARE_CLASSES.append( 'django.middleware.cache.FetchFromCacheMiddleware' )
