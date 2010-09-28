from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from Users.models import DoesNotExists as UserDoesNotExist

class RestAuthException( Exception ):
	code = 500
	body = 'If you get this text, file a bugreport!'

	def __init__( self, body=None ):
		if body:
			self.body = body

class UsernameInvalid( RestAuthException ):
	code = 400

class ServiceNotFound( RestAuthException ):
	code = 500

class PasswordInvalid( RestAuthException ):
	code = 400

class ResourceExists( RestAuthException ):
	code = 409

class ContentTypeNotAcceptable( RestAuthException ):
	code = 406

class MarshallError( RestAuthException ):
	code = 500

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
	except Exception as e:
		raise MarshalError( e )

CONTENT_TYPES = [ 'application/json', 'text/plain' ]

def get_response_type( request ):
	try:
		if request.META['HTTP_ACCEPT'] == '*/*':
			accept = CONTENT_TYPES
		else:
			accept = request.META['HTTP_ACCEPT'].split( ',' )
	except KeyError:
		accept = CONTENT_TYPES

	try:
		request_type = request.META['CONTENT_TYPE']
	except KeyError:
		request_type = None

	# neither Content-Type nor Accept header:
	if not request_type and not accept:
		return 'application/json'
	
	if not accept: # no accept header
		if request_type in CONTENT_TYPES:
			return request_type
		else:
			raise ContentTypeNotAcceptable( "Unacceptable content type requested: The Content-Type header is unsupported and no Accept header was provided" )

	# No Content-Type header, but there is an Accept value that we can produce:
	if not request_type:
		acceptable = [ typ for typ in accept if typ in CONTENT_TYPES ]
		if acceptable:
			return acceptable[0]
		else:
			raise ContentTypeNotAcceptable( "Unacceptable content type requested: The Accept-Header lists no acceptable content type" )
	
	if request_type and request_type in accept:
		return request_type

	if request_type not in accept:
		raise ContentTypeNotAcceptable( 'Unable to determine content-type' );

class RestAuthMiddleware:
	def process_exception( self, request, exception ):
		if isinstance( exception, ObjectDoesNotExist ):
			print( 'ObjectDoesNotExists: %s'%(dir( exception )) )
			print( exception.__class__ )
			print( exception.__module__ ) # str!
			return HttpResponse( exception, status=404 )
		if isinstance( exception, RestAuthException ):
			body = exception.body
			status = exception.code
			return HttpResponse( body, status=status )
