import datetime
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User, get_hexdigest
from django.utils.translation import ugettext_lazy as _

class InvalidPostData( BaseException ):
	pass

def check_valid_username( username ):
	if hasattr( settings, 'MIN_USERNAME_LENGTH' ):
		min_length = settings.MIN_USERNAME_LENGTH
	else:
		min_length = 3

	if not username.isalnum():
		raise InvalidPostData( "Username must be alphanumeric" )
	if len( username ) < min_length:
		raise InvalidPostData( "Username too short" )

def check_valid_password( password ):
	if hasattr( settings, 'MIN_PASSWORD_LENGTH' ):
		min_length = settings.MIN_PASSWORD_LENGTH
	else:
		min_length = 6
	
	if len( password ) < min_length:
		raise InvalidPostData( "Password too short" )

	return True

# Create your models here.
class ServiceUser( models.Model ):
	username = models.CharField(_('username'), max_length=30, unique=True, help_text=_("Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters"))
	algorithm = models.CharField( _('algorithm'), max_length=5, help_text=_("The algorithm used to hash passwords") )
	salt = models.CharField( _('salt'), max_length=16, help_text=_("salt for the hash") )
	hash = models.CharField( _('hash'), max_length=128, help_text=_("actual hash of the password") )
# original:
#	password = models.CharField(_('password'), max_length=128, help_text=_("Use '[algo]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>."))
	last_login = models.DateTimeField(_('last login'), default=datetime.datetime.now, auto_now=True)
	date_joined = models.DateTimeField(_('date joined'), default=datetime.datetime.now)

	def set_password( self, raw_password ):
		if hasattr( settings, 'DEFAULT_PASSWORD_HASH_ALGORITHM' ):
			self.algorithm = settings.DEFAULT_PASSWORD_HASH_ALGORITHM
		else:
			self.algorithm = 'sha1'

		import random
		self.salt = get_hexdigest(self.algorithm, str(random.random()), str(random.random()))[:5]
		self.hash = get_hexdigest(self.algorithm, self.salt, raw_password)

	def set_unusable_password( self ):
		self.hash = None
		self.salt = None
		self.algorithm = None

	def check_password( self, raw_password ):
		return self.hash == get_hexdigest( self.algorithm, self.salt, raw_password )
