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

import logging
from RestAuthCommon.error import BadRequest, RestAuthException, UnsupportedMediaType, NotAcceptable
from RestAuthCommon.handlers import CONTENT_HANDLERS

def get_request_type( request ):
	import mimeparse
	supported = CONTENT_HANDLERS.keys()

	header = request.META['CONTENT_TYPE']
	match = mimeparse.best_match( supported, header )
	if match:
		return match
	else:
		raise UnsupportedMediaType()

def get_response_type( request ):
	import mimeparse
	from RestAuthCommon.handlers import CONTENT_HANDLERS
	supported = CONTENT_HANDLERS.keys()

	header = request.META['HTTP_ACCEPT']
	match = mimeparse.best_match( supported, header )
	if match:
		return match
	else:
		raise NotAcceptable()

def get_dict( request, keys=[], optional=[] ):
	"""
	Unmarshal a dictionary and verify that this dictionary only contains the specified
	I{keys}. If I{keys} only contains one element, this method returns just
	the string, otherwise it returns the unmarshalled dictionary.

	This method primarily exists as as a means to ensure standars compliance
	of clients in the reference service implementation. Using this method,
	the server will throw an error if the client sends any unknown keys.

	@param request: The request that should be parsed.
	@type  request: HttpRequest
	@param    keys: The keys that the dictionary should contain.
	@type     keys: list

	@return: Either the values of specified I{keys} (in order) or the value
		if I{keys} contains just one value.
	@rtype: list/str
	@raise BadRequest: If the data was not parsable as the format specified
		by the 'Content-Type' header, if the data was not a dictionary
		or the data did not contain the keys specified.
	@raise NotAcceptable: If the ContentType header of the request did not
		indicate a supported format.
	"""
	from RestAuthCommon.error import UnmarshalError

	try:
		mime_type = get_request_type( request )
		body = request.raw_post_data
		
		handler = CONTENT_HANDLERS[mime_type]()
		data = handler.unmarshal_dict( body )
	except UnmarshalError as e:
		raise BadRequest( e )

	# check for mandatory parameters:
	key_set = set(data.keys())
	if not set(keys).issubset( key_set ):
		raise BadRequest( "Did not find expected keys in string" )
	# check for unknown parameters:
	optional_parameters = key_set.difference( set(keys) )
	if not optional_parameters.issubset( optional ):
		raise BadRequest( "Did not find expected keys in string" )
		
	if len( keys ) == 1 and not optional:
		return data[keys[0]]
	else:   
		return [ data[key] for key in keys ] + [ data.pop(key, None) for key in optional ]
