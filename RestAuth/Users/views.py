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

from RestAuth.Services.decorator import login_required
from RestAuth.Users.models import *
from RestAuth.common.types import get_dict
from RestAuth.common.responses import *

from django.http import HttpResponse

@login_required(realm="/users/")
def index( request ):
	service = request.user.username

	if request.method == "GET": # get list of users:
		names = [ user.username for user in ServiceUser.objects.all() ]
		
		logging.debug( "%s: Got list of users"%(service) )
		return HttpRestAuthResponse( request, names )
	elif request.method == 'POST': # create new user:
		# If BadRequest: 400 Bad Request
		name, password = get_dict( request, [u'user', u'password'] )
		
		# If ResourceExists: 409 Conflict
		# If UsernameInvalid: 412 Precondition Failed
		# If PasswordInvalid: 412 Precondition Failed
		user = user_create( name, password )
		
		logging.info( "%s: Created user '%s'"%(service, user.username) )
		return HttpResponseCreated( request, user )
	
	return HttpResponse( status=405 )

@login_required(realm="/users/<user>/")
def user_handler( request, username ):
	service = request.user.username
	username = username.lower()
	
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )

	if request.method == 'GET': # Verify that a user exists:
		logging.debug( "%s: Check if user '%s' exists"%(service, user.username) )
		return HttpResponseNoContent() # OK
	elif request.method == 'POST': # verify password
		# If BadRequest: 400 Bad Request
		password = get_dict( request, [ u'password' ] )

		if not user.check_password( password ):
			# password does not match - raises 404
			raise ServiceUser.DoesNotExist( "Password invalid for this user." )
		user.save() # update "modified" timestamp, perhaps hash
		
		logging.debug( "%s: Checked password for user '%s'"%(service, username ) )
		return HttpResponseNoContent() # Ok
	elif request.method == 'PUT': # Change password
		# If BadRequest: 400 Bad Request
		password = get_dict( request, [ u'password' ] )

		# If UsernameInvalid: 412 Precondition Failed
		user.set_password( password )
		user.save()
		
		logging.debug( "%s: Update password for user '%s'"%(service, username ) )
		return HttpResponseNoContent()
	elif request.method == 'DELETE': # delete a user:
		user.delete()

		logging.info( "%s: Deleted user '%s'"%(service, username ) )
		return HttpResponseNoContent()
	
	return HttpResponse( status=405 ) # Method Not Allowed


@login_required(realm="/users/<user>/props/")
def userprops_index( request, username ):
	service = request.user.username
	
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )

	if request.method == 'GET': # get all properties
		props = user.get_properties()
		
		logging.debug( "%s: Get properties for '%s'"%(service, username) )
		return HttpRestAuthResponse( request, props )
	elif request.method == 'POST': # create property
		# If BadRequest: 400 Bad Request
		prop, value = get_dict( request, [ u'prop', u'value' ] )

		# If PropertyExists: 409 Conflict
		prop = user.add_property( prop, value )

		logging.info( "%s: Created property '%s' for '%s'"%(service, prop, username ) )
		return HttpResponseCreated( request, prop )
	
	return HttpResponse( status=405 ) # Method Not Allowed

@login_required(realm="/users/<user>/props/<prop>/")
def userprops_prop( request, username, prop ):
	service = request.user.username
	
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )
	
	if request.method == 'GET': # get value of a property
		# If Property.DoesNotExist: 404 Not Found
		prop = user.get_property( prop )

		logging.debug( "%s: Got property '%s' for '%s'"%(service, prop, username) )
		return HttpRestAuthResponse( request, prop.value )

	elif request.method == 'PUT': # Set property
		# If BadRequest: 400 Bad Request
		value = get_dict( request, [ u'value' ] )

		prop, old_value = user.set_property( prop, value )
		if old_value.__class__ == unicode: # property previously defined:
			return HttpRestAuthResponse( request, old_value )
		else: # new property:
			return HttpResponseCreated( request, prop )

	elif request.method == 'DELETE': # Delete property:
		# If Property.DoesNotExist: 404 Not Found
		user.del_property( prop )

		logging.info( "%s: Delete property '%s' for user '%s'"%(service, prop, username) )
		return HttpResponseNoContent()
	
	return HttpResponse( status=405 ) # Method Not Allowed
