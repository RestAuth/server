from RestAuth.BasicAuth.decorator import require_basicauth
from RestAuth.Users.models import *

from RestAuth.common import get_setting, marshal, parse_request_body

from django.http import HttpResponse, QueryDict
from django.http.multipartparser import MultiPartParser

@require_basicauth("Create ServiceUser")
def create( request ):
	"""
	This handles /users/:
	POST: create a new ServiceUser, returns HTTP status code:
		201: created
		400: bad request (i.e. POST-data is invalid/missing)
		403: forbidden (not allowed for client)
		409: conflict (user already exists)
		500: internal server error (i.e. uncought exception)
	else: return 405 (method not allowed)
	"""
	if request.method == "GET":
		# get list of users
		users = ServiceUser.objects.all()
		names = [ user.username for user in users ]
		response = marshal( request, names )
		return HttpResponse( response )
	elif request.method == 'POST':
		body = parse_request_body( request )

		# add a user
		try:
			username = body['user'].lower()
			password = body['password']
		except KeyError:
			return HttpResponse( 'Could not retrieve username/password from POST data', status=400 )

		# If UsernameInvalid: 400 Bad Request
		check_valid_username( username )
		check_valid_password( password )

		# If ResourceExists: 409 Conflict
		user_create( username, password )
		return HttpResponse( status=201 )
	else:
		return HttpResponse( status=405 )

@require_basicauth("Handle ServiceUser")
def user_handler( request, username ):
	username = username.lower()
	# If UsernameInvalid: 400 Bad Request
	check_valid_username( username )
	
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )

	if request.method == 'DELETE':
		# delete a user
		user.delete()
		return HttpResponse( status=200 ) # OK
	elif request.method == 'POST':
		# check users credentials
		body = parse_request_body( request )

		try:
			password = body['password']
		except KeyError:
			return HttpResponse( status=400 ) # Bad Request

		if user.check_password( password ):
			user.save() # update "modified" timestamp
			return HttpResponse( status=200 ) # Ok
		else:
			# password does not match - raises 404
			raise ServiceUser.DoesNotExist( "Password invalid for this user." )

	elif request.method == 'PUT':
		# update the users credentials

		can_change_name = get_setting( 'ALLOW_USERNAME_CHANGE', False )
		body = parse_request_body( request )
		
		# Check validity of request data:
		if len( body ) == 0:
			return HttpResponse( status=400 ) # Bad Request
		if can_change_name and 'user' in body:
			check_valid_username( body['user'].lower() )
		elif 'user' in body:
			return HttpResponse( "Changing the username is not allowed with this RestAuth installation.", status=412 )
		if 'password' in body:
			check_valid_password( body['password'] )

		# update credentials
		if 'user' in body:
			user.username = body['user'].lower()
		if 'password' in body:
			user.set_password( body['password'] )

		user.save()
		return HttpResponse( status=200 ) # Ok
	elif request.method == 'GET':
		# Check if a user exists 
		# (If user doesn't exist, we already returned 404)
		return HttpResponse( status=200 ) # OK
	else:
		# mmmh, exotic HTTP method!
		return HttpResponse( status=405 ) # Method Not Allowed


#@require_basicauth("Userproperties index")
def userprops_index( request, username ):
	# If UsernameInvalid: 400 Bad Request
	check_valid_username( username )
	
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )

	if request.method == 'GET':
		props = user.get_properties()
		return HttpResponse( marshal( request, props ) )
	elif request.method == 'POST':
		body = parse_request_body( request )

		if 'prop' not in body and 'value' not in body:
			# We check for this right away so we don't cause any
			# database load in case this happens
			return HttpResponse( status=400 )

		if user.has_property( body['prop'] ):
			return HttpResponse( 'Property already set', status=409 )
		else:
			user.set_property( body['prop'], body['value'] )
			return HttpResponse()
	else:
		return HttpResponse( status=405 ) # Method Not Allowed

#@require_basicauth("Userproperties prop")
def userprops_prop( request, username, prop ):
	# If UsernameInvalid: 400 Bad Request
	check_valid_username( username )
	
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )
	
	if request.method == 'GET':
		prop = user.get_property( prop )
		return HttpResponse( prop.value )
	elif request.method == 'PUT':
		body = parse_request_body( request )
		if 'value' not in body:
			# We check for this right away so we don't cause any
			# database load in case this happens
			return HttpResponse( status=400 )

		user.set_property( prop, body['value'] )
		return HttpResponse()
	elif request.method == 'DELETE':
		user.del_property( prop )
		return HttpResponse() 
	else:
		return HttpResponse( status=405 ) # Method Not Allowed
