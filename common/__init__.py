from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from errors import BadRequest

def parse_request_body( request ):
	if request.has_key( 'Content-Type' ):
		content_type = request['Content-Type']
	else:
		content_type = 'application/x-www-form-urlencoded'

	if content_type == 'application/x-www-form-urlencoded':
		if request.method == 'POST':
			return request.POST
		elif request.method == 'PUT':
			return QueryDict( request.raw_post_data, encoding=request._encoding)
	elif content_type == 'application/json':
		import json
		print( type( request.raw_post_data ) )
		json.loads( request.raw_post_data )
	else:
		raise BadRequest( 'Content-Type is unacceptable: %s'%(content_type) )

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
