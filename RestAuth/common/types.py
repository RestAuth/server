import logging
from errors import ContentTypeNotAcceptable, BadRequest
import mimeparse

class content_handler( object ):
	def get_str( self, body ):
		pass
	def get_dict( self, body, keys ):
		pass
	def get_list( self, body ):
		pass
	def get_bool( self, body ):
		pass

	def serialize_str( self, obj ):
		pass
	def serialize_bool( self, obj ):
		pass
	def serialize_list( self, obj ):
		pass
	def serialize_dict( self, obj ):
		pass

class json_handler( content_handler ):
	def __init__( self ):
		import json
		self.json = json

	def get_str( self, body ):
		return self.json.loads( body )

	def get_dict( self, body, encoding ):
		return self.json.loads( body, encoding )

	def get_list( self, body ):
		return self.json.loads( body )

	def get_bool( self, body ):
		return self.json.loads( body )
	
	def serialize_str( self, obj ):
		return self.json.dumps( obj )

	def serialize_bool( self, obj ):
		return self.json.dumps( obj )

	def serialize_list( self, obj ):
		return self.json.dumps( obj )

	def serialize_dict( self, obj ):
		return self.json.dumps( obj )

class form_handler( content_handler ):
	def get_dict( self, body ):
		return QueryDict( body, encoding=request.encoding)

	def serialize_str( self, obj ):
		return obj

	def serialize_bool( self, obj ):
		if obj:
			return "1"
		else:
			return "0"

	def serialize_dict( self, obj ):
		d = QueryDict('', True )
		d.update( obj )
		return d.urlencode()

	def serialize_list( self, obj ):
		d = dict( [ ('key%s'%i, obj[i]) for i in range(0,len(obj)) ] )
		return self.serialize_dict( d )

class xml_handler( content_handler ):
	pass

CONTENT_HANDLERS = { 'application/json': json_handler, 
	'application/xml': xml_handler,
	'application/x-www-form-urlencoded': form_handler }

def get_data( request, typ ):
	content_type = request.META['CONTENT_TYPE']
	if content_type not in CONTENT_HANDLERS:
		raise ContentTypeNotAcceptable()

	handler_obj = CONTENT_HANDLERS[content_type]()
	func = getattr( handler_obj, 'get_%s'%(typ.__name__) )
	try:
		val = func( request.raw_post_data, request.encoding )
	except BadRequest as e:
		raise e
	except Exception as e:
		raise BadRequest( "Request body unparsable: %s"%(e) )
	if val.__class__ != typ:
		raise BadRequest( "Request body contained %s instead of %s"
			%(val.__class__, typ) )

	return val

def get_dict( request, keys ):
	"""
	Get a dictionary with the specified keys from the body of the request.

	This method takes care of parsing the dictionary. It will throw a
	L{BadRequest} if the dictionary does not contain the exact keys
	specified.
	If the parameter keys contains only a single value, this method returns
	a string, if it contains multiple values, the method will return a list
	with the values of the list in the order specified by keys.

	@param request: The request that should be parsed.
	@type  request: HttpRequest
	@param    keys: The keys that the dictionary should contain.
	@type     keys: list

	@return: The values of the keys specified.
	@rtype: str or list
	@raise BadRequest: If the data was not parsable as the format specified
		by the 'Content-Type' header, if the data was not a dictionary
		or the data did not contain the keys specified.
	"""
	val = get_data( request, dict )
	if sorted(keys) != sorted(val.keys()):
		raise BadRequest()
	if len( keys ) == 1:
		return val[keys[0]]
	else:
		return [ val[key] for key in keys ]

def serialize( request, obj ):
	header = request.META['HTTP_ACCEPT']
	match = mimeparse.best_match( CONTENT_HANDLERS.keys(), header )
	handler = CONTENT_HANDLERS[match]()
	func_name = 'serialize_%s'%(obj.__class__.__name__)

	try:
		func = getattr( handler, func_name )
		return func( obj )
	except Exception as e:
		raise MarshalError( e )
