from django.http import HttpResponse

class ResourceNotFound( Exception ):
	pass

class ResourceExists( Exception ):
	pass

class ContentTypeNotAcceptable( Exception ):
	pass

class MarshallError( Exception ):
	pass

def get_response_type( request ):
	try:
		if request.META['HTTP_ACCEPT'] == '*/*':
			accept = []
		else:
			accept = request.META['HTTP_ACCEPT'].split( ',' )
	except KeyError:
		accept = []

	try:
		request_type = request.META['CONTENT_TYPE']
	except KeyError:
		request_type = None

	if not request_type and not accept:
		return 'text/plain'
	
	if not accept:
		return request_type
	if not request_type:
		return accept[0]
	
	if request_type and request_type in accept:
		return request_type

	if request_type not in accept:
		raise ContentTypeNotAcceptable();

class ContentTypeNotAcceptableMiddleware:
	def process_exception( self, request, exception ):
		if len( exception.args ) > 0:
			response = HttpResponse( exception.args[0] )
		else:
			response = HttpResponse()

		if isinstance( exception, ContentTypeNotAcceptable ):
			response.status_code = 406
		elif isinstance( exception, ResourceNotFound ):
			response.status_code = 404
		elif isinstance( exception, ResourceExists ):
			response.status_code = 409
		elif isinstance( exception, MarshallError ):
			response.status_code = 500

		if response.status_code != 200:
			return response
