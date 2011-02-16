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

from django.utils.encoding import smart_str
import hashlib

def get_salt():
	"""
	Get a very random salt. The salt is the first eight characters of a
	sha512 hash of 5 random numbers concatenated.
	"""
	from random import random
	random_string = ','.join( map( lambda a: str(random()), range(5) ) )
	return hashlib.sha512( random_string ).hexdigest()[:8]

def get_hexdigest( algorithm, salt, secret ):
	"""
	This method overrides the standard get_hexdigest method for service
	users. It adds support for for the 'mediawiki' hash-type and any
	crypto-algorithm included in the hashlib module.

	Unlike the django function, this function requires python2.5 or higher.
	"""
	salt, secret = smart_str(salt), smart_str(secret)
	if algorithm == 'mediawiki':
		secret_hash = hashlib.md5( secret ).hexdigest()
		return hashlib.md5( '%s-%s'%(salt, secret_hash ) ).hexdigest()
	else:
		return getattr( hashlib, algorithm )( salt + secret ).hexdigest()
