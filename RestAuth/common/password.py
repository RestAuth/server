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