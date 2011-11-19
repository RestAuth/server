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

from django.utils.encoding import smart_str
import hashlib, crypt

def crypt_apr1_md5( plainpasswd, salt ):
	"""
	This function creates an md5 hash that is identical to one that would be created by
	:py:cmd:`htpasswd -m`.
	
	Algorithm shamelessly copied from here:
		http://www.php.net/manual/de/function.crypt.php#73619
	"""
	import struct, base64, string
	def pack( val ):
		md5 = hashlib.md5( val ).hexdigest()
		return struct.pack('16B', *[int(c, 16) for c in (md5[i:i+2] for i in xrange(0, len(md5), 2))])
	
	length = len( plainpasswd )
	text = "%s$apr1$%s"%(plainpasswd, salt)
	md5 = hashlib.md5( "%s%s%s"%(plainpasswd, salt, plainpasswd) ).hexdigest()
	bin = pack( "%s%s%s"%(plainpasswd, salt, plainpasswd) )
	
	# first loop
	i = len( plainpasswd )
	while i > 0:
		text += bin[0:min(16,i)]
		i -= 16
		
	# second loop
	i = len( plainpasswd )
	while i > 0:
		if i & 1:
			text += chr(0)
		else:
			text += plainpasswd[0]
			
		# shift bits by one (/2 rounded down)
		i >>= 1
	
	# 1000er loop
	bin = pack( text )
	for i in range(0, 1000):
		if i & 1:
			new = plainpasswd
		else:
			new = bin

		if i % 3:
			new += salt
		if i % 7:
			new += plainpasswd
		
		if i & 1:
			new += bin
		else:
			new += plainpasswd

		bin = pack( new )

	tmp = ''
	for i in range(0, 5):
		k = i+6
		j = i+12
		if j == 16:
			j = 5
		
		tmp = "%s%s%s%s"%(bin[i], bin[k], bin[j], tmp)

	tmp = "%s%s%s%s"%(chr(0), chr(0), bin[11], tmp)
	
	frm = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
	to = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
	trans = string.maketrans( frm, to )
	return base64.b64encode( tmp )[2:][::-1].translate( trans )

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
	secret = smart_str(secret)
	if salt:
		salt = smart_str(salt)
		
	if algorithm == 'mediawiki': # pragma: no cover
		secret_hash = hashlib.md5( secret ).hexdigest()
		return hashlib.md5( '%s-%s'%(salt, secret_hash ) ).hexdigest()
	elif algorithm == 'crypt':
		if '$' in salt:
			return crypt.crypt( secret, salt ).rsplit('$', 1)[1]
		else:
			return crypt.crypt( secret, salt )[2:]
	elif algorithm == 'apr1':
		return crypt_apr1_md5( secret, salt ).encode( 'utf-8' )
	else:
		func = getattr( hashlib, algorithm )
		if salt:
			return func( salt + secret ).hexdigest()
		else:
			return func( secret ).hexdigest()