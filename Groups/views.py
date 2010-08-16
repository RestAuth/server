from RestAuth.BasicAuth.decorator import require_basicauth
from RestAuth.Users.models import *
from RestAuth.Groups.models import *
from RestAuth.common import *
from django.http import HttpResponse, QueryDict

@require_basicauth( "group management" )
def index( request ):
	project = request.user

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
			groups = user.get_groups( project, recursive )
		else:
			# get all groups for this project
			groups = Group.objects.filter( project=project )

		names = [ group.name for group in groups ]
		# If MarshalError: 500 Internal Server Error
		response = marshal( request, names )
		return HttpResponse( response, status=200 ) # Ok
	elif request.method == 'POST':
		# add a new group
		if 'group' in request.POST:
			name = request.POST['group']
		else:
			return HttpResponse( status=400 ) # Bad request

		# If ResourceExists: 409 Conflict
		group_create( project, name )
		return HttpResponse( status=201 ) # Created
	else:
		return HttpResponse( status=405 ) # method not allowed

@require_basicauth( "group management" )
def group_handler( request, groupname ):
	project = request.user
	
	# If ResourceNotFound: 404 Not Found
	group = group_get( project=project, name=groupname )

	if request.method == 'GET':
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
				group_create( project, groupname )
			except ResourceExists:
				# This is not an error
				pass

		if 'user' in request.POST: # add a user to a group
			# If ResourceNotFound: 404 Not Found
			user = user_get( request.POST['user'] )
			group.users.add( user )
		elif 'group' in request.POST: # add a group to a group
			# If ResourceNotFound: 404 Not Found
			childgroup = group_get( project, request.POST['group'] )
			group.groups.add( childgroup )
		
		group.save()
		return HttpResponse( status=200 )
	elif request.method == 'DELETE':
		group.delete()
		return HttpResponse( status=200 ) # OK
	else:
		return HttpResponse( status=405 )

@require_basicauth( "group management" )
def member_handler( request, groupname, username ):
	project = request.user
	
	# If ResourceNotFound: 404 Not Found
	group = group_get( project, groupname )
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
