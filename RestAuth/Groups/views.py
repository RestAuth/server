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

from RestAuth.Services.decorator import login_required
from RestAuth.Users.models import *
from RestAuth.Groups.models import *
from RestAuth.common.types import get_dict
from RestAuth.common.responses import *
from django.http import HttpResponse
import logging

@login_required( realm='/groups/' )
def index( request ):
	service = request.user
	logger = logging.getLogger( 'groups' )

	if request.method == 'GET' and 'user' in request.GET: 
		# Get all users in a group
		username = request.GET['user']
			
		# If User.DoesNotExist: 404 Not Found
		user = user_get( username ) 

		groups = user.get_groups( service )
		names = [ group.name for group in groups ]

		logger.debug( '%s: Get groups for user %s'%(service, username) )
		return HttpRestAuthResponse( request, names ) # Ok
	elif request.method == 'GET': # Get a list of groups:
		# get all groups for this service
		groups = Group.objects.filter( service=service )

		names = [ group.name for group in groups ]
		logger.debug( '%s: Get all groups'%(service) )
		return HttpRestAuthResponse( request, names ) # Ok
	elif request.method == 'POST': # Create a group
		# If BadRequest: 400 Bad Request
		groupname = get_dict( request, [ u'group' ] )

		# If ResourceExists: 409 Conflict
		group = group_create( groupname, service )
		
		logger.info( '%s: Create group %s'%( service, groupname ) )
		return HttpResponseCreated( request, group ) # Created
	
	logger.error( '%s: Method not allowed: %s'%(service, request.method) )
	return HttpResponse( status=405 ) # method not allowed

@login_required( realm='/groups/<group>/' )
def group_handler( request, groupname ):
	service = request.user
	logger = logging.getLogger( 'groups.group' )
	
	# If Group.DoesNotExist: 404 Not Found
	group = group_get( groupname, service )
	
	if request.method == 'GET': # Verify that a group exists:
		logger.debug( "%s: Check if group %s exists"%(service, groupname) )
		return HttpResponseNoContent()
	if request.method == 'DELETE': # Delete group
		group.delete()
		logger.info( "%s: Deleted group %s"%(service, groupname) )
		return HttpResponseNoContent() # OK
	
	logger.error( '%s: Method not allowed: %s'%(service, request.method) )
	return HttpResponse( status=405 )

@login_required( realm='/groups/<group>/users/' )
def group_users_index_handler( request, groupname ):
	service = request.user
	logger = logging.getLogger( 'groups.group.users' )
	
	# If Group.DoesNotExist: 404 Not Found
	group = group_get( groupname, service )

	if request.method == 'GET': # Get all users in a group
		users = group.get_members()
		usernames = [ user.username for user in users ]

		# If MarshalError: 500 Internal Server Error
		logger.debug( "Get users in group '%s'"%(group.name) )
		return HttpRestAuthResponse( request, usernames )
	elif request.method == 'POST': # Add a user to a group
		# If BadRequest: 400 Bad Request
		username = get_dict( request, [ u'user' ] )
		
		# If User.DoesNotExist: 404 Not Found
		user = user_get( username )
		
		group.users.add( user )
		group.save()

		logger.info( '%s: Add user "%s" to group "%s"'%(service, username, group.name) )
		return HttpResponseNoContent()
	
	logger.error( '%s: Method not allowed: %s'%(service, request.method) )
	return HttpResponse( status=405 )

@login_required( realm='/groups/<group>/users/<user>/' )
def group_user_handler( request, groupname, username ):
	service = request.user
	logger = logging.getLogger( 'groups.group.users.user' )
	
	# If Group.DoesNotExist: 404 Not Found
	group = group_get( groupname, service )
	# If User.DoesNotExist: 404 Not Found
	user = user_get( username )
	
	if request.method == 'GET': # Verify that a user is in a group
		logger.debug( '%s: Check if user "%s" is in group "%s"'%(service, group.name, user.username) )
		if group.is_member( user ):
			return HttpResponseNoContent()
		else:
			# 404 Not Found
			raise ServiceUser.DoesNotExist()
	elif request.method == 'DELETE': # Remove user from a group
		if not group.is_member( user, False ):
			raise User.DoesNotExist()

		group.users.remove( user )
		logger.info( '%s: Remove user "%s" from group "%s"'%(service, user.username, group.name) )
		return HttpResponseNoContent()

	logger.error( '%s: Method not allowed: %s'%(service, request.method) )
	return HttpResponse( status=405 )

@login_required( realm='/groups/<group>/groups/' )
def group_groups_index_handler( request, groupname ):
	service = request.user
	logger = logging.getLogger( 'groups.group.groups' )
	
	# If Group.DoesNotExist: 404 Not Found
	group = group_get( groupname, service )
	if request.method == 'GET': # get a list of sub-groups
		groups = group.groups.filter( service=service )

		groupnames = [ group.name for group in groups ] 
		# If MarshalError: 500 Internal Server Error
		logger.debug( '%s: %s: Get subgroups'%(service, group.name) )
		return HttpRestAuthResponse( request, groupnames )
	elif request.method == 'POST': # Add a sub-group:
		# If BadRequest: 400 Bad Request
		sub_groupname = get_dict( request, [ u'group' ] )
		
		# If Group.DoesNotExist: 404 Not Found
		sub_group = group_get( sub_groupname, service )
		
		group.groups.add( sub_group )
		group.save()
		logger.info( '%s: %s: Add subgroup %s'%(service, group.name, sub_group.name) )
		return HttpResponseNoContent()

	logger.error( '%s: Method not allowed: %s'%(service, request.method) )
	return HttpResponse( status=405 )

@login_required( realm='/groups/<meta-group>/groups/<sub-group>/' )
def group_groups_handler( request, meta_groupname, sub_groupname ):
	service = request.user
	logger = logging.getLogger( 'groups.group.groups.subgroup' )
	
	# If Group.DoesNotExist: 404 Not Found
	meta_group = group_get( meta_groupname, service )
	# If Group.DoesNotExist: 404 Not Found
	sub_group = group_get( sub_groupname, service )

	if request.method == 'DELETE': # Remove group from a group
		if not meta_group.groups.filter( name=sub_groupname ).exists():
			raise Group.DoesNotExist()

		meta_group.groups.remove( sub_group )
		logger.info( '%s: %s: Remove subgroup %s'%(service, meta_group.name, sub_group.name) )
		return HttpResponseNoContent()
	
	logger.error( '%s: Method not allowed: %s'%(service, request.method) )
	return HttpResponse( status=405 )
