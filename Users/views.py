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
			username = request.POST['username']
			password = request.POST['password']
		except KeyError:
			return HttpResponse( 'Could not retrieve username/password from POST data', status=400 )

		# If UsernameInvalid: 400 Bad Request
		check_valid_username( username )
		check_valid_password( password )
	
		if ServiceUser.objects.filter( username=username ).exists():
			return HttpResponse( status=409 )

		user = ServiceUser( username=username )
		user.set_password( password )
		user.save()
		return HttpResponse( status=201 )
	else:
		return HttpResponse( status=405 )

@require_basicauth("Handle ServiceUser")
def user_handler( request, username ):
	# If UsernameInvalid: 400 Bad Request
	check_valid_username( username )

	if request.method == 'DELETE':
		# delete a user
		try:
			user = ServiceUser.objects.get( username=username )
			user.delete()
			return HttpResponse( status=200 ) # OK
		except ServiceUser.DoesNotExist:
			return HttpResponse( status=404 ) # Not Found
		except:
			return HttpResponse( status=500 ) # Internal Server Error
	elif request.method == 'POST':
		# check users credentials

		try:
			password = request.POST['password']
		except KeyError:
			return HttpResponse( status=400 ) # Bad Request

		try:
			user = ServiceUser.objects.get( username=username )
			if user.check_password( password ):
				user.save() # update "modified" timestamp
				return HttpResponse( status=200 ) # Ok
			else:
				# password does not match
				return HttpResponse( status=404 ) # Not found
		except ServiceUser.DoesNotExist:
			# user does not exist
			return HttpResponse( status=404 ) # Not found
		except:
			return HttpResponse( status=500 ) # Internal Server Error

	elif request.method == 'PUT':
		# update the users credentials

		put_data = QueryDict( request.raw_post_data, encoding=request._encoding)
		if len( put_data ) == 0:
			return HttpResponse( status=400 ) # Bad Request

		try:
			user = ServiceUser.objects.get( username=username )
		except ServiceUser.DoesNotExist:
			return HttpResponse( status=404 ) # Not Found

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
		try:
			ServiceUser.objects.get( username=username )
			return HttpResponse( status=200 ) # OK
		except ServiceUser.DoesNotExist:
			return HttpResponse( status=404 ) # Not Found
		except:
			return HttpResponse( status=500 ) # Internal Server Error
	else:
		# mmmh, exotic HTTP method!
		return HttpResponse( status=405 ) # Method Not Allowed

	# Unreachable
	return HttpResponse( status=500 ) # Internal Server Error
