from RestAuth.BasicAuth.decorator import require_basicauth
from RestAuth.UserAuth.models import *

from django.shortcuts import get_object_or_404, render_to_response
from django.conf import settings
from django.http import HttpResponse, QueryDict
from django.http.multipartparser import MultiPartParser

#@require_basicauth("Create ServiceUser")
def create( request ):
	"""
	This handles /users:
	POST: create a new ServiceUser, returns HTTP status code:
		201: created
		400: bad request (i.e. POST-data is invalid/missing)
		403: forbidden (not allowed for client)
		409: conflict (user already exists)
		500: internal server error (i.e. uncought exception)
	else: return 405 (method not allowed)
	"""
	import sys
	if request.method != 'POST':
		return HttpResponse( status=405 )
	
	try:
		username = request.POST['username']
		password = request.POST['password']
	except KeyError:
		return HttpResponse( status=400 )

	try:
		check_valid_username( username )
		check_valid_password( password )
	except InvalidPostData as e:
		return HttpResponse( e.args[0] + "\n", status=400 )
	
	try:
		user = ServiceUser.objects.get( username=username )
		return HttpResponse( status=409 )
	except ServiceUser.DoesNotExist:
		pass
	except Exception, e:
		return HttpResponse( str(e), status=500 )

	user = ServiceUser( username=username )
	user.set_password( password )
	user.save()
	return HttpResponse( status=201 )

#@require_basicauth("Handle ServiceUser")
def user_handler( request, username ):
	print request.META.get('HTTP_CONTENT_TYPE', request.META.get('CONTENT_TYPE', ''))
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
		print( len(put_data) )
		if len( put_data ) == 0:
			return HttpResponse( status=400 ) # Bad Request

		try:
			user = ServiceUser.objects.get( username=username )
		except ServiceUser.DoesNotExist:
			return HttpResponse( status=404 ) # Not Found

		if hasattr( settings, 'ALLOW_USERNAME_CHANGE' ) and settings.ALLOW_USERNAME_CHANGE:
			if put_data.has_key( 'username' ):
				try:
					check_valid_username( put_data['username'] )
				except InvalidPostData as e:
					return HttpResponse( e.args[0] + "\n", status=400 ) # Bad Request
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
	else:
		return HttpResponse( status=405 ) # Method Not Allowed

	# Unreachable
	return HttpResponse( status=500 ) # Internal Server Error
