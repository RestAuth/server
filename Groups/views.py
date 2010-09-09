from RestAuth.BasicAuth.decorator import require_basicauth
from RestAuth.Users.models import *
from RestAuth.Groups.models import *
from RestAuth.common import *
from django.http import HttpResponse, QueryDict

import sys

@require_basicauth( "group management" )
def index( request ):
	service = request.user

	if request.method == 'GET':
		if 'user' in request.GET:
			# get groups for a specific user
			
			# If ResourceNotFound: 404 Not Found
			user = user_get( request.GET['user'] ) 
			if 'nonrecursive' in request.GET:
				recursive = False
			else:
				recursive = True

			# If ResourceNotFound: 404 Not Found
			groups = user.get_groups( service, recursive )
		else:
			# get all groups for this service
			groups = Group.objects.filter( service=service )

		names = [ group.name for group in groups ]
		# If MarshalError: 500 Internal Server Error
		response = marshal( request, names )
		return HttpResponse( response, status=200 ) # Ok
	elif request.method == 'POST':
		# add a new group
		if 'group' in request.POST:
			groupname = request.POST['group']
		else:
			return HttpResponse( status=400 ) # Bad request

		# If ResourceExists: 409 Conflict
		group_create( groupname, service )
		return HttpResponse( status=201 ) # Created
	else:
		return HttpResponse( status=405 ) # method not allowed

@require_basicauth( "group management" )
def group_handler( request, groupname ):
	service = request.user
	
	if request.method == 'GET':
		# If ResourceNotFound: 404 Not Found
		group = group_get( groupname, service )

		# get all members of a group
		if 'nonrecursive' in request.GET:
			recursive = False
		else:
			recursive = True
		
		users = group.get_members( recursive )

		# If MarshalError: 500 Internal Server Error
		response = marshal( request, [ user.username for user in users ] )
		return HttpResponse( response, status=200 )
	elif request.method == 'POST':
		if 'user' not in request.POST and 'group' not in request.POST:
			# We check for this right away so we don't cause any
			# database load in case this happens
			return HttpResponse( status=400 )

		if 'autocreate' in request.POST:
			try:
				group = group_create( groupname, service )
			except ResourceExists:
				# If ResourceNotFound: 404 Not Found
				group = group_get( groupname, service )
		else:
			# If ResourceNotFound: 404 Not Found
			group = group_get( groupname, service )
			

		if 'user' in request.POST: # add a user to a group
			# If ResourceNotFound: 404 Not Found
			user = user_get( request.POST['user'] )
			group.users.add( user )
		elif 'group' in request.POST: # add a group to a group
			# If ResourceNotFound: 404 Not Found
			childgroup = group_get( request.POST['group'], service )
			group.groups.add( childgroup )
		
		group.save()
		return HttpResponse( status=200 )
	elif request.method == 'DELETE':
		# If ResourceNotFound: 404 Not Found
		group = group_get( groupname, service )
		group.delete()
		return HttpResponse( status=200 ) # OK
	else:
		return HttpResponse( status=405 )

@require_basicauth( "group management" )
def member_handler( request, groupname, username ):
	service = request.user
	
	# If ResourceNotFound: 404 Not Found
	group = group_get( groupname, service )
	user = user_get( username )

	if request.method == 'GET':
		if 'nonrecursive' in request.GET:
			recursive = False
		else:
			recursive = True

		if group.is_member( user, recursive ):
			return HttpResponse( status=200 )
		else:
			return HttpResponse( 'not in group', status=404 ) # Not Found
	elif request.method == 'DELETE':
		group.users.remove( user )
		return HttpResponse( status=200 )
	else:
		return HttpResponse( status=405 )
