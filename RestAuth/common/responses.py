from django.http import HttpResponse

class HttpResponseCreated( HttpResponse ):
	def __init__( self, request, entity ):
# TODO: make_list of body
		location = entity.get_absolute_url()
		uri = request.build_absolute_uri( location )
		HttpResponse.__init__( self, uri, status=201 )
		self['Location'] = uri
