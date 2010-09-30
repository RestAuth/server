class RestAuthException( Exception ):
	code = 500
	body = 'If you get this text, file a bugreport!'

	def __init__( self, body=None ):
		if body:
			self.body = body

class ServiceNotFound( RestAuthException ):
	code = 500

class BadRequest( RestAuthException ):
	code = 400

class PasswordInvalid( BadRequest ):
	pass

class UsernameInvalid( BadRequest ):
	pass

class ResourceExists( RestAuthException ):
	code = 409

class ContentTypeNotAcceptable( RestAuthException ):
	code = 406

class MarshalError( RestAuthException ):
	code = 500
