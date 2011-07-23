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
