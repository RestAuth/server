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
