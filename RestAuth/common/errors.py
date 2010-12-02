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

class PreconditionFailed( RestAuthException ):
	code = 412

class PasswordInvalid( PreconditionFailed ):
	pass

class UsernameInvalid( PreconditionFailed ):
	pass

class ResourceExists( RestAuthException ):
	code = 409

class ContentTypeNotAcceptable( RestAuthException ):
	code = 406

class MarshalError( RestAuthException ):
	code = 500
