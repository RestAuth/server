# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
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

import sys, base64
from RestAuth.Services.models import Service
from django.contrib.auth.models import User

class InternalAuthenticationBackend:
	supports_anonymous_user = False
	supports_object_permissions = False
	
	def authenticate( self, header, host ):
		"""
		Authenticate against a header as send by HTTP basic
		authentication and a host. This method takes care of decoding
		the header.
		"""
		method, data = header.split()
		if method.lower() != 'basic': # pragma: no cover
			return None # we only support basic authentication

		name, password = base64.b64decode(data).split(':')

		try:
			serv = Service.objects.get( username=name )
			if serv.verify( password, host ):
				# service successfully verified
				return serv
		except Service.DoesNotExist:
			# service does not exist
			return None

	def get_user( self, user_id ): # pragma: no cover
		"""
		Get the user by id. This is used by clients that implement
		sessions.
		"""
		return Service.objects.get( id=user_id )
