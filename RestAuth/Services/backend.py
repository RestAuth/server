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
		if method.lower() != 'basic':
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

	def get_user( self, user_id ):
		"""
		Get the user by id. This is used by clients that implement
		sessions.
		"""
		return Service.objects.get( id=user_id )
