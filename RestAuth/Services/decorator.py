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

from django.http import HttpResponse
from django.contrib.auth import authenticate, login

def login_user( view, request, realm, *args, **kwargs ):
	"""
	The function called when the login_user decorator is used.
	"""
	if request.user.is_authenticated():
		return view(request, *args, **kwargs)

	if 'REMOTE_USER' in request.META:
		# The web-server already authenticated the remote user:
		user = authenticate( remote_user=request.META['REMOTE_USER'] )
	if 'HTTP_AUTHORIZATION' in request.META:
		# The web-server does *not* handle authentication and the client
		# tries to authenticate.
		header = request.META['HTTP_AUTHORIZATION']
		host = request.META['REMOTE_ADDR']
		user = authenticate( header=header, host=host )

	if user:
		# log the user in:
		login(request, user)
		return view(request, *args, **kwargs)
	else:
		# send an authentication challenge:
		response = HttpResponse( "Please authenticate", status=401 )
		response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
		return response

def login_required( function = None, realm = "" ):
	"""
	Define our own login_required decorator to handle basic authentication,
	performed either by the webserver or the decorator itself.
	"""
	def view_decorator(func):
		def wrapper(request, *args, **kwargs):
			return login_user(func, request, realm, *args, **kwargs)
		return wrapper
	return view_decorator
