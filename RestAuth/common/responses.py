from django.http import HttpResponse
from RestAuth.common.types import serialize

class HttpResponseCreated( HttpResponse ):
	def __init__( self, request, entity ):
# TODO: make_list of body
		location = entity.get_absolute_url()
		uri = request.build_absolute_uri( location )

		# RFC 2616 defines body as a list:
		body = serialize( request, [ uri ] )

		HttpResponse.__init__( self, body, status=201 )
		self['Location'] = uri
