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

import base64

from django.contrib.auth.models import User

from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, get_backends

from RestAuth.BasicAuth.models import ServiceAddress
from RestAuth.common import get_setting

def verify_hostname( username, address ):
	try:
		hostname = ServiceAddress.objects.get( address=address )
		if hostname.services.filter( username=username ).exists():
			return True
		else:
			return False
	except ServiceAddress.DoesNotExist:
		return False

def auth_request( realm, body='please authenticate' ):
	# Either they did not provide an authorization header or
	# something in the authorization attempt failed. Send a 401
	# back to them to ask them to authenticate.
	#
	response = HttpResponse( body, status=401 )
	response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
	return response

#############################################################################
#
def view_or_basicauth(view, request, test_func, realm = "", *args, **kwargs):
	"""
	This is a helper function used by both 'logged_in_or_basicauth' and
	'has_perm_or_basicauth' that does the nitty of determining if they
	are already logged in or if they have provided proper http-authorization
	and returning the view if all goes well, otherwise responding with a 401.
	"""
	# Check if it is even possible to authenticate from this host:
	remote_addr = request.META['REMOTE_ADDR']
	if not ServiceAddress.objects.filter( address=remote_addr ).exists():
		# This means that its impossible for the HTTP client to
		# authenticate, no matter what credentials are provided
		return HttpResponse( 'no service is allowed to authenticate from %s'%(remote_addr), status=403 )

	# Check if we are already authenticated:
	if request.user.is_authenticated():
		return view(request, *args, **kwargs)

	# get auth_provider
	auth_provider = get_setting( 'AUTH_PROVIDER', 'internal' )

	if auth_provider == 'apache':
		# The credentials of the service were verified by the webserver,
		# we only need to log the user in:
		if 'REMOTE_USER' in request.META:
			username = request.META['REMOTE_USER']

			try:
				user = User.objects.get( username=username )
				backend = get_backends()[0]
				user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
				login( request, user )
				request.user = user
				return view(request, *args, **kwargs)
			except User.DoesNotExist:
				msg = "The webserver authenticated to a username that is unknown in the local database."
				return HttpResponse( msg, status=500 )

	elif auth_provider == 'internal':
		# RestAuth should also handle service authentication:
		if 'HTTP_AUTHORIZATION' in request.META:
			method, data = request.META['HTTP_AUTHORIZATION'].split()
			if method.lower() == "basic":
				username, passwd = base64.b64decode(data).split(':')
				if not verify_hostname( username, remote_addr ):
					msg = '%s is not allowed to authenticate from %s'%(username, remote_addr)
					return auth_request( realm, msg )

				user = authenticate( username=username, password=passwd )
				if user is not None:
					login(request, user)
					request.user = user
					return view(request, *args, **kwargs)
	else:
		return HttpResponse( 'Unknown AUTH_PROVIDER', status=500 )

	# If we reach this, no authentication credentials were provided or
	# authentication failed
	return auth_request( realm )

	
#############################################################################
#
def require_basicauth(realm = ""):
	"""
	A simple decorator that requires a user to be logged in. If they are not
	logged in the request is examined for a 'authorization' header.

	If the header is present it is tested for basic authentication and
	the user is logged in with the provided credentials.

	If the header is not present a http 401 is sent back to the
	requestor to provide credentials.

	The purpose of this is that in several django projects I have needed
	several specific views that need to support basic authentication, yet the
	web site as a whole used django's provided authentication.

	The uses for this are for urls that are access programmatically such as
	by rss feed readers, yet the view requires a user to be logged in. Many rss
	readers support supplying the authentication credentials via http basic
	auth (and they do NOT support a redirect to a form where they post a
	username/password.)

	Use is simple:

	@logged_in_or_basicauth
	def your_view:
		...

	You can provide the name of the realm to ask for authentication within.
	"""
	def view_decorator(func):
		def wrapper(request, *args, **kwargs):
			return view_or_basicauth(func, request,
					realm, *args, **kwargs)
		return wrapper
	return view_decorator
