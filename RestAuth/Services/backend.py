import sys, base64
from RestAuth.Services.models import Service

class InternalAuthenticationBackend:
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

				
