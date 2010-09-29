from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from errors import BadRequest

def parse_request_body( request ):
	"""
	Parse the request body of POST and PUT requests according to the format
	indicated by the 'Content-Type' header. Currently, either
	'application/json' or 'x-www-form-urlencoded' is supported. If the
	header is missing, the data is assumed to be of type
	'x-www-form-urlencoded'. 

	@param request: The request as passed to the django invocation handler
	@raise BadRequest: When the request could not be parsed or *any*
		Exception is thrown.

	"""
	if request.META.has_key( 'CONTENT_TYPE' ):
		content_type = request.META['CONTENT_TYPE']
	else:
		content_type = 'application/x-www-form-urlencoded'

	try:
		if content_type == 'application/x-www-form-urlencoded':
			if request.method == 'POST':
				return request.POST
			elif request.method == 'PUT':
				return QueryDict( request.raw_post_data, encoding=request._encoding)
		elif content_type == 'application/json':
			import json
			return json.loads( request.raw_post_data )
	except Exception as e:
		print( 'Ex: %s'%(e) )
		print( request.raw_post_data )
		raise BadRequest( 'Error parsing body: %s'%(e) )

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
		print( e )
		raise e
	except Exception as e:
		print( e )
		raise MarshalError( e )

CONTENT_TYPES = [ 'application/json', 'application/x-www-form-urlencoded' ]

def get_response_type( request ):
	# parse HTTP-Accept header:
	if 'HTTP_ACCEPT' in request.META:
		# parse HTTP-Accept header:
		header = request.META['HTTP_ACCEPT']
		if not header or header == ['*/*']:
			accept = CONTENT_TYPES
		else:
			accept = header.split( ',' )

			# filter types not acceptable to us:
			accept = [ typ for typ in accept if typ in CONTENT_TYPES ]
	else:
		# no header, default to application/json:
		return 'application/json'

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
