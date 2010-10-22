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

import datetime
from django.db import models
from django.db.utils import IntegrityError
from django.contrib.auth.models import User, get_hexdigest
from django.utils.translation import ugettext_lazy as _
from RestAuth.common import get_setting, get_hexdigest, get_salt
from RestAuth.common.errors import UsernameInvalid, PasswordInvalid, ResourceExists
from RestAuth.Users import validators

class PropertyExists( ResourceExists ):
	pass

def user_exists( name ):
	if ServiceUser.objects.filter( username=name ).exists():
		return True
	else:
		return False

def user_get( name ):
	return ServiceUser.objects.get( username=name )

def user_create( name, password ):
	try:
		user = ServiceUser( username=name )
		user.set_password( password )
		user.save()
		return user
	except IntegrityError:
		raise ResourceExists( "A user with the given name already exists." )

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

class ServiceUser( models.Model ):
	username = models.CharField(_('username'), max_length=30, unique=True, help_text=_("Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters"))
	algorithm = models.CharField( _('algorithm'), max_length=20, help_text=_("The algorithm used to hash passwords") )
	salt = models.CharField( _('salt'), max_length=16, help_text=_("salt for the hash") )
	hash = models.CharField( _('hash'), max_length=128, help_text=_("actual hash of the password") )
	last_login = models.DateTimeField(_('last login'), default=datetime.datetime.now, auto_now=True)
	date_joined = models.DateTimeField(_('date joined'), default=datetime.datetime.now)

	def set_password( self, raw_password ):
		self.algorithm = get_setting( 'HASH_ALGORITHM', 'sha1' )
		self.salt = get_salt()
		self.hash = get_hexdigest( self.algorithm, self.salt, raw_password )

	def set_unusable_password( self ):
		self.hash = None
		self.salt = None
		self.algorithm = None

	def check_password( self, raw_password ):
		return self.hash == get_hexdigest( self.algorithm, self.salt, raw_password )

	def get_groups( self, service=None, recursive=True ):
		"""
		Get a list of groups that this user is a member of.

		@param service: Limit the list of groups to those defined by the
			given service.
		@type  service: service
		"""
		if service:
			groups = set( self.group_set.filter( service=service ) )
		else:
			groups = set( self.group_set.all() )

		if recursive:
			# import here to avoid circular imports:
			from RestAuth.Groups.models import Group

			# get groups that this user is only an indirect member
			# of. 
			all_groups = Group.objects.filter( service=service )
			for group in all_groups:
				if group in groups:
					continue

				if group.is_indirect_member( self ):
					groups.add( group )

			# get child-groups
			child_groups = set()
			for group in groups:
				child_groups.update( group.get_child_groups() )
			groups.update( child_groups )

		return groups

	def has_property( self, key ):
		if self.property_set.filter( key=key ).exists():
			return True
		else:
			return False

	def add_property( self, key, value ):
		"""
		Add a new property to this user. It is an error if this property
		already exists.

		@raises PropertyExists: If the property already exists.
		"""
		try:
			self.property_set.add( Property( key=key, value=value ) )
		except IntegrityError:
			raise PropertyExists( key )		

	def get_properties( self ):
		dictionary = {}

		props = self.property_set.all()
		for prop in props:
			dictionary[prop.key] = prop.value
		return dictionary

	def set_property( self, key, value ):
		"""
		Set the property identified by I{key} to I{value}. If the
		property already exists, it is overwritten.
		"""
		try:
			# This issues a plain INSERT, which throws an 
			# IntegrityError if the property already exists:
			self.property_set.add( Property( key=key, value=value ) )
		except IntegrityError:
			# This means that the property already exists. 
			# since user and key are unique, this is guaranteed to
			# only update the right key.
			self.property_set.filter( key=key ).update( value=value )

	def get_property( self, key ):
		"""
		@raises Property.DoesNotExist: When the property does not exist.
		"""
		# exactly one SELECT statement
		return self.property_set.get( key=key )
	
	def del_property( self, key ):
		try:
			self.get_property( key ).delete()
		except Property.DoesNotExist:
			pass

	def __unicode__( self ):
		return self.username

class Property( models.Model ):
	user = models.ForeignKey( ServiceUser )
	key = models.CharField( max_length=30 )
	value = models.CharField( max_length=100 )

	class Meta:
		unique_together = ( 'user', 'key' )

	def __unicode__( self ):
		return "%s: %s=%s"%(self.user.username, self.key, self.value)
