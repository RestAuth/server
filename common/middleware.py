"""
The ExceptionMiddleware is located in its own class to avoid circular imports.
"""

from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from RestAuth.common.errors import RestAuthException
from RestAuth.Users.models import ServiceUser, Property
from RestAuth.Groups.models import Group

class ExceptionMiddleware:
	def process_exception( self, request, exception ):
		if isinstance( exception, ServiceUser.DoesNotExist ):
			print( 'ServiceUser.DoesNotExist: %s'%(exception) )
			resp = HttpResponse( exception, status=404 )
			resp['Resource'] = 'User'
			return resp
		if isinstance( exception, Group.DoesNotExist ):
			resp = HttpResponse( exception, status=404 )
			resp['Resource'] = 'Group'
			return resp
		if isinstance( exception, Property.DoesNotExist ):
			resp = HttpResponse( exception, status=404 )
			resp['Resource'] = 'Property'
			return resp

		if isinstance( exception, RestAuthException ):
			body = exception.body
			status = exception.code
			return HttpResponse( body, status=status )
