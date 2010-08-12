import base64

from django.contrib.auth.models import User

from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, get_backends

#############################################################################
#
def view_or_basicauth(view, request, test_func, realm = "", *args, **kwargs):
	"""
	This is a helper function used by both 'logged_in_or_basicauth' and
	'has_perm_or_basicauth' that does the nitty of determining if they
	are already logged in or if they have provided proper http-authorization
	and returning the view if all goes well, otherwise responding with a 401.
	"""
	if not hasattr( settings, 'RESTAUTH_AUTH_PROVIDER' ):
		# we definetly depend on this setting
		return HttpResponse( "You must set RESTAUTH_AUTH_PROVIDER in localsettings.py!", status=500 )

	# Check if the remote address is allowed to make any requests at all
	if hasattr( settings, 'RESTAUTH_ALLOWED_HOSTS' ):
		allowed_hosts = settings.RESTAUTH_ALLOWED_HOSTS
	else:
		allowed_hosts = ['127.0.0.1']
	if request.META['REMOTE_ADDR'] not in allowed_hosts:
		return HttpResponse( status=403 )
	
	# Check if we are already authenticated:
	if request.user.is_authenticated():
		return view(request, *args, **kwargs)

	if settings.RESTAUTH_AUTH_PROVIDER == 'apache':
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

	if settings.RESTAUTH_AUTH_PROVIDER == 'internal':
		# RestAuth should also handle service authentication:
		if 'HTTP_AUTHORIZATION' in request.META:
			method, data = request.META['HTTP_AUTHORIZATION'].split()
			if method.lower() == "basic":
				uname, passwd = base64.b64decode(data).split(':')
				user = authenticate(username=uname, password=passwd)
				if user is not None:
					print( 'd' )
					login(request, user)
					request.user = user
					return view(request, *args, **kwargs)

	# Either they did not provide an authorization header or
	# something in the authorization attempt failed. Send a 401
	# back to them to ask them to authenticate.
	#
	response = HttpResponse( "AUTH failed, headers: " + ', '.join( request.META ) )
	response.status_code = 401
	response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
	return response
	
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
