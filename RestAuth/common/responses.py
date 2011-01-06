from django.http import HttpResponse as HttpResponseBase
from RestAuth.common.types import get_response_type

class HttpRestAuthResponse( HttpResponseBase ):
	def __init__( self, request, response_object, status=200 ):
		from RestAuthCommon import marshal

		mime_type = get_response_type( request )
		body = marshal( mime_type, response_object )

		HttpResponseBase.__init__( self, body, mime_type, status, mime_type )

class HttpResponseNoContent( HttpRestAuthResponse ):
	def __init__( self ):
		HttpResponseBase.__init__( self, status=204 )

class HttpResponseCreated( HttpRestAuthResponse ):
	def __init__( self, request, entity ):
		location = entity.get_absolute_url()
		uri = request.build_absolute_uri( location )

		HttpRestAuthResponse.__init__( self, request, [ uri ], 201 )
		self['Location'] = uri
