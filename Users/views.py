from RestAuth.BasicAuth.decorator import require_basicauth
from RestAuth.Users.models import *
from RestAuth.common import *

from django.shortcuts import get_object_or_404, render_to_response
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
		# add a user
		try:
			username = request.POST['user']
			password = request.POST['password']
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
	# If UsernameInvalid: 400 Bad Request
	check_valid_username( username )
	
	# If ResourceNotFound: 404 Not Found
	user = user_get( username )

	if request.method == 'DELETE':
		# delete a user
		user.delete()
		return HttpResponse( status=200 ) # OK
	elif request.method == 'POST':
		# check users credentials

		try:
			password = request.POST['password']
		except KeyError:
			return HttpResponse( status=400 ) # Bad Request

		if user.check_password( password ):
			user.save() # update "modified" timestamp
			return HttpResponse( status=200 ) # Ok
		else:
			# password does not match
			return HttpResponse( status=404 ) # Not found

	elif request.method == 'PUT':
		# update the users credentials

		put_data = QueryDict( request.raw_post_data, encoding=request._encoding)
		if len( put_data ) == 0:
			return HttpResponse( status=400 ) # Bad Request

		if get_setting( 'ALLOW_USERNAME_CHANGE', False ):
			if put_data.has_key( 'username' ):
				# If UsernameInvalid: 400 Bad Request
				check_valid_username( put_data['username'] )
				user.username = put_data['username']
		else:
			if put_data.has_key( 'username' ):
				return HttpResponse( status=403 ) # Forbidden

		if put_data.has_key( 'password' ):
			try:
				check_valid_password( put_data['password'] )
			except InvalidPostData as e:
				return HttpResponse( e.args[0] + "\n", status=400 ) # Bad Request

			user.set_password( put_data['password'] )

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
	
	# If ResourceNotFound: 404 Not Found
	user = user_get( username )

	if request.method == 'GET':
		props = user.get_properties()
		return HttpResponse( marshal( request, props ) )
	elif request.method == 'POST':
		if 'prop' not in request.POST and 'value' not in request.POST:
			# We check for this right away so we don't cause any
			# database load in case this happens
			return HttpResponse( status=400 )

		if user.has_property( request.POST['prop'] ):
			return HttpResponse( 'Property already set', status=409 )
		else:
			user.set_property( request.POST['prop'], request.POST['value'] )
			return HttpResponse()
	else:
		return HttpResponse( status=405 ) # Method Not Allowed

#@require_basicauth("Userproperties prop")
def userprops_prop( request, username, prop ):
	# If UsernameInvalid: 400 Bad Request
	check_valid_username( username )
	
	# If ResourceNotFound: 404 Not Found
	user = user_get( username )
	
	if request.method == 'GET':
		prop = user.get_property( prop )
		return HttpResponse( prop.value )
	elif request.method == 'PUT':
		put_data = QueryDict( request.raw_post_data, encoding=request._encoding)
		if 'value' not in put_data:
			# We check for this right away so we don't cause any
			# database load in case this happens
			return HttpResponse( status=400 )

		user.set_property( prop, put_data['value'] )
		return HttpResponse()
	elif request.method == 'DELETE':
		user.del_property( prop )
		return HttpResponse() 
	else:
		return HttpResponse( status=405 ) # Method Not Allowed
