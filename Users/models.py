import datetime
from django.db import models
from django.contrib.auth.models import User, get_hexdigest
from django.utils.translation import ugettext_lazy as _
from RestAuth.common import ResourceNotFound, get_setting, UsernameInvalid, PasswordInvalid, ResourceExists
from RestAuth.Users import validators

def user_exists( name ):
	if ServiceUser.objects.filter( username=name ).exists():
		return True
	else:
		return False

def user_get( name ):
	try:
		return ServiceUser.objects.get( username=name )
	except ServiceUser.DoesNotExist:
		raise ResourceNotFound( 'user not found' )

def user_create( name, password ):
	if user_exists( name ):
		raise ResourceExists( "A user with the given name already exists." )
	
	user = ServiceUser( username=name )
	user.set_password( password )
	user.save()
	

def check_valid_username( username ):
	min_length = get_setting( 'MIN_USERNAME_LENGTH', 3 )
	max_length = get_setting( 'MAX_USERNAME_LENGTH', 255 )
	if len( username ) < min_length:
		raise UsernameInvalid( "Username too short" )
	if len( username ) > max_length:
		raise UsernameInvalid( "Username too long" )

	skip_validators = get_setting( 'SKIP_VALIDATORS', [] )
	for val in [ f for f in dir( validators ) ]:
		if val in skip_validators:
			continue

		func = getattr( validators, val )
		if not callable( func ):
			continue

		if not func( username ):
			raise UsernameInvalid( 'Username is not valid on %s'%(val) )


def check_valid_password( password ):
	min_length = get_setting( 'MIN_PASSWORD_LENGTH', 6 )
	
	if len( password ) < min_length:
		raise PasswordInvalid( "Password too short" )

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
		self.algorithm = get_setting( 'HASH_ALGORITHM', 'sha1' )

		import random
		self.salt = get_hexdigest(self.algorithm, str(random.random()), str(random.random()))[:5]
		self.hash = get_hexdigest(self.algorithm, self.salt, raw_password)

	def set_unusable_password( self ):
		self.hash = None
		self.salt = None
		self.algorithm = None

	def check_password( self, raw_password ):
		return self.hash == get_hexdigest( self.algorithm, self.salt, raw_password )

	def get_groups( self, project=None, recursive=True ):
		if project:
			groups = list( self.group_set.filter( service=project ) )
		else:
			groups = list( self.group_set.all() )

		if recursive:
			# import here to avoid circular imports:
			from RestAuth.Groups.models import Group

			# get groups that this user is only an indirect member
			# of. 
			all_groups = Group.objects.filter( service=project )
			for group in all_groups:
				if group in groups:
					continue

				if group.is_indirect_member( self ):
					groups.append( group )

			# get child-groups
			for group in groups:
				child_groups = group.get_child_groups()
				groups += ( child_groups )

		return groups
