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

from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str
import hashlib

from errors import BadRequest, ContentTypeNotAcceptable, MarshalError

def get_setting( setting, default=None ):
	if hasattr( settings, setting ):
		return getattr( settings, setting )
	else:
		return default

def marshal( request, obj ):
	try:   
		response_type = get_response_type( request )
		if response_type == 'text/plain':
			return ', '.join( obj )
		elif response_type == 'application/json':
			import json
			return json.dumps( obj )
		else:  
			raise ContentTypeNotAcceptable('Failed to determine an acceptable content-type! (%s)'%(response_type) )
	except ContentTypeNotAcceptable as e:
		raise e
#	except Exception as e:
#		raise MarshalError( e )

CONTENT_TYPES = [ 'application/json', 'application/x-www-form-urlencoded' ]

def get_response_type( request ):
	# parse HTTP-Accept header:
	if 'HTTP_ACCEPT' in request.META:
		# parse HTTP-Accept header:
		header = request.META['HTTP_ACCEPT']
		if not header or header == '*/*':
			accept = CONTENT_TYPES
		else:
			accept = header.split( ',' )

			# filter types not acceptable to us:
			accept = [ typ for typ in accept if typ in CONTENT_TYPES ]
	else:
		# no header, default to application/json:
		return 'application/json'

	if not accept:
		raise ContentTypeNotAcceptable( "Accept-Header did not list any acceptable mime types: '%s'"%(header) )

	if len( accept ) == 1:
		# Most of the time, the client will tell us one format to use
		if accept[0] in CONTENT_TYPES:
			# if we only accept one content type and its acceptable
			# to us, we use that
			return accept[0]
		else:
			raise ContentTypeNotAcceptable( "No acceptable mime type was provided by the HTTP-Accept header." )
	
	# The client accepts more than one format:
	if 'CONTENT_TYPE' in request.META:
		if request.META['CONTENT_TYPE'] in accept:
			# If the Content-Type used by the client is acceptable,
			# we return that:
			return request.META['CONTENT_TYPE']
		else:
			return accept[0]
	else:
		return accept[0]

	raise ContentTypeNotAcceptable( "Could not determine response content-type!" )

def get_salt():
	"""
	Get a very random salt. The salt is the first eight characters of a
	sha512 hash of 5 random numbers concatenated.
	"""
	from random import random
	random_string = ','.join( map( lambda a: str(random()), range(5) ) )
	return hashlib.sha512( random_string ).hexdigest()[:8]

def get_hexdigest( algorithm, salt, secret ):
	"""
	This method overrides the standard get_hexdigest method for service
	users. It adds support for for the 'mediawiki' hash-type and any
	crypto-algorithm included in the hashlib module.

	Unlike the django function, this function requires python2.5 or higher.
	"""
	salt, secret = smart_str(salt), smart_str(secret)
	if algorithm == 'mediawiki':
		return hashlib.md5( '%s-%s'%(salt, secret ) ).hexdigest()
	else:
		return getattr( hashlib, algorithm )( salt + secret ).hexdigest()
