import logging
from errors import RestAuthException, UnsupportedMediaType, NotAcceptable, BadRequest

def get_request_type( request ):
	import mimeparse
	from RestAuthCommon import CONTENT_HANDLERS
	supported = CONTENT_HANDLERS.keys()

	header = request.META['CONTENT_TYPE']
	match = mimeparse.best_match( supported, header )
	if match:
		return match
	else:
		raise NotAcceptable()

def get_response_type( request ):
	import mimeparse
	from RestAuthCommon import CONTENT_HANDLERS
	supported = CONTENT_HANDLERS.keys()

	header = request.META['HTTP_ACCEPT']
	match = mimeparse.best_match( supported, header )
	if match:
		return match
	else:
		raise UnsupportedMediaType()

def get_dict( request, keys ):
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
	from RestAuthCommon import unmarshal
	from RestAuthCommon.handlers import UnmarshalError

	try:
		mime_type = get_request_type( request )
		body = request.raw_post_data
		data = unmarshal( mime_type, body, dict )
	except UnmarshalError as e:
		raise BadRequest( e )
	except RestAuthException as e:
		raise e

	if sorted( keys ) != sorted( data.keys() ):
		raise BadRequest( "Did not find expected keys in string" )
	if len( keys ) == 1:
		return data[keys[0]]
	else:   
		return [ data[key] for key in keys ]
