class RestAuthException( Exception ):
	code = 500
	body = 'If you get this text, file a bugreport!'

	def __init__( self, body=None ):
		if body:
			self.body = body

class UsernameInvalid( RestAuthException ):
	code = 400

class ServiceNotFound( RestAuthException ):
	code = 500

class PasswordInvalid( RestAuthException ):
	code = 400

class ResourceExists( RestAuthException ):
	code = 409

class ContentTypeNotAcceptable( RestAuthException ):
	code = 406

class MarshallError( RestAuthException ):
	code = 500
