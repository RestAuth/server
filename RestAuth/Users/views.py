# This file is part of RestAuth (http://fs.fsinf.at/wiki/RestAuth).
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

from RestAuth.BasicAuth.decorator import login_required
from RestAuth.Users.models import *
from RestAuth.common import get_setting, marshal, parse_request_body

from django.http import HttpResponse, QueryDict
from django.http.multipartparser import MultiPartParser

@login_required(realm="/users/")
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
	service = request.user.username

	if request.method == "GET":
		# get list of users
		users = ServiceUser.objects.all()
		names = [ user.username for user in users ]
		response = marshal( request, names )
		logging.debug( "%s: Got list of users"%(service) )
		return HttpResponse( response )
	elif request.method == 'POST':
		body = parse_request_body( request )

		# add a user
		try:
			username = body['user'].lower()
			password = body['password']
		except KeyError:
			logging.error( "%s: Bad POST body: %s"%(service, request.raw_post_data) )
			return HttpResponse( 'Could not retrieve username/password from POST data', status=400 )

		# If UsernameInvalid: 400 Bad Request
		check_valid_username( username )
		check_valid_password( password )

		# If ResourceExists: 409 Conflict
		user_create( username, password )
		logging.info( "%s: Created user '%s'"%(service, username) )
		return HttpResponse( status=201 )
	else:
		return HttpResponse( status=405 )

@login_required(realm="/users/<user>/")
def user_handler( request, username ):
	service = request.user.username
	username = username.lower()
	
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )

	if request.method == 'DELETE':
		# delete a user
		user.delete()
		logging.info( "%s: Deleted user '%s'"%(service, username ) )
		return HttpResponse( status=200 ) # OK
	elif request.method == 'POST':
		# check users credentials
		body = parse_request_body( request )

		try:
			password = body['password']
		except KeyError:
			logging.error( "%s: Bad POST body: %s"%(service, request.raw_post_data) )
			return HttpResponse( status=400 ) # Bad Request

		logging.debug( "%s: Check password for user '%s'"%(service, username ) )

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
			logging.error( "%s: Bad PUT data: []"%(service) )
			return HttpResponse( status=400 ) # Bad Request
		if can_change_name and 'user' in body:
			check_valid_username( body['user'].lower() )
		elif 'user' in body:
			logging.error( "%s: Changing username is not allowed."%(service) )
			return HttpResponse( "Changing the username is not allowed with this RestAuth installation.", status=412 )
		if 'password' in body:
			check_valid_password( body['password'] )

		# update credentials
		if 'user' in body:
			old_name = user.username
			user.username = body['user'].lower()
			logging.info( "%s: Renamed user '%s' to '%s'"%(service, user.username, old_name) )
		if 'password' in body:
			user.set_password( body['password'] )
			logging.info( "%s: Updated password for '%s'"%(service, user.username ) )

		user.save()
		return HttpResponse( status=200 ) # Ok
	elif request.method == 'GET':
		# Check if a user exists 
		# (If user doesn't exist, we already returned 404)
		logging.debug( "%s: Check if user '%s' exists"%(service, user.username) )
		return HttpResponse( status=200 ) # OK
	else:
		# mmmh, exotic HTTP method!
		return HttpResponse( status=405 ) # Method Not Allowed


@login_required(realm="/users/<user>/props/")
def userprops_index( request, username ):
	service = request.user.username
	
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )

	if request.method == 'GET':
		props = user.get_properties()
		logging.debug( "%s: Get properties for '%s'"%(service, username) )
		return HttpResponse( marshal( request, props ) )
	elif request.method == 'POST':
		body = parse_request_body( request )

		if 'prop' not in body and 'value' not in body:
			# We check for this right away so we don't cause any
			# database load in case this happens
			logging.error( "%s: Bad POST body: %s"%(service, request.raw_post_data) )
			return HttpResponse( status=400 )

		user.add_property( body['prop'], body['value'] )
		logging.info( "%s: Set '%s'='%s' for '%s'"%(service, body['prop'], body['value'], username ) )
		return HttpResponse()
	else:
		return HttpResponse( status=405 ) # Method Not Allowed

@login_required(realm="/users/<user>/props/<prop>/")
def userprops_prop( request, username, prop ):
	service = request.user.username
	
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )
	
	if request.method == 'GET':
		prop = user.get_property( prop )
		logging.debug( "%s: Got property '%s' for '%s'"%(service, prop, username) )
		return HttpResponse( prop.value )
	elif request.method == 'PUT':
		body = parse_request_body( request )
		if 'value' not in body:
			# We check for this right away so we don't cause any
			# database load in case this happens
			logging.critical( "%s: Bad PUT body: %s"%(service, request.raw_post_data) )
			return HttpResponse( status=400 )

		user.set_property( prop, body['value'] )
		logging.info( "%s: Set property '%s' for user '%s'"%(service, prop, username) )
		return HttpResponse()
	elif request.method == 'DELETE':
		user.del_property( prop )
		logging.info( "%s: Deleted property '%s' for user '%s'"%(service, prop, username) )
		return HttpResponse() 
	else:
		return HttpResponse( status=405 ) # Method Not Allowed
