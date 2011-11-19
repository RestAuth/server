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

import re, datetime, stringprep
from django.conf import settings
from django.contrib.auth.models import User
from django.core import exceptions
from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlquote
from django.utils.importlib import import_module

from RestAuth.common.password import get_hexdigest, get_salt
from RestAuth.common.errors import UsernameInvalid, PasswordInvalid, UserExists, PropertyExists
from RestAuth.Users import validators
from RestAuthCommon.error import PreconditionFailed


def user_get( name ):
	"""
	Get a user with the given username.
	
	Note: this is only used by the CLI interface any more.

	@raises ServiceUser.DoesNotExist: When the user does not exist.
	"""
	return ServiceUser.objects.get( username=name.lower() )

def user_create( name, password ):
	"""
	Creates a new user. Lowercases the username.

	@raise UserExists: If the user already exists
	@raise UsernameInvalid: If the username is unacceptable
	@raise PasswordInvalid: If the password is unacceptable
	"""
	name = name.lower()
	validate_username( name )
	try:
		user = ServiceUser( username=name )
		if password: 
			user.set_password( password )
		user.save()
		return user
	except IntegrityError:
		raise UserExists( "A user with the given name already exists." )

def validate_username( username ):
	if len( username ) < settings.MIN_USERNAME_LENGTH:
		raise UsernameInvalid( "Username too short" )
	if len( username ) > settings.MAX_USERNAME_LENGTH:
		raise UsernameInvalid( "Username too long" )
		
	illegal_chars = set()
	reserved = set()
	force_ascii = False
	allow_whitespace = True
	validators = []
	
	for validator_path in settings.VALIDATORS:
		# import validator:
		try:
			modname, classname = validator_path.rsplit('.', 1)
		except ValueError:
			raise exceptions.ImproperlyConfigured(
				'%s isn\'t a middleware module' % validator_path )
		
		try:
			mod = import_module( modname )
		except ImportError as e:
			raise exceptions.ImproperlyConfigured(
				'Error importing middleware %s: "%s"' % (modname, e))
		try:
			validator = getattr( mod, classname )
		except AttributeError:
			raise exceptions.ImproperlyConfigured(
				'Middleware module "%s" does not define a "%s" class' % (modname, classname))
		
		if hasattr( validator, 'check' ):
			validators.append( validator )
		
		illegal_chars |= validator.ILLEGAL_CHARACTERS
		reserved |= validator.RESERVED
		if validator.FORCE_ASCII:
			force_ascii = True
		if not validator.ALLOW_WHITESPACE:
			allow_whitespace = False
	
	# check for illegal characters:
	for char in illegal_chars:
		if char in username:
			raise UsernameInvalid( "Username must not contain character '%s'"%char )

	# reserved names
	if username in reserved:
		raise UsernameInvalid( "Username is reserved" )
	
	# force ascii if necessary
	if force_ascii:
		try:
			username.decode( 'ascii' )
		except UnicodeDecodeError:
			raise UsernameInvalid( "Username must only contain ASCII characters" )
	
	# check for whitespace
	if not allow_whitespace:
		if force_ascii:
			whitespace_regex = re.compile( '\s' )
		else:
			whitespace_regex = re.compile( '\s', re.UNICODE )
		if whitespace_regex.search( username ):
			raise UsernameInvalid( "Username must not contain any whitespace" )

	for validator in validators:
		validator.check( username )

class ServiceUser( models.Model ):
	username = models.CharField(_('username'), max_length=60, unique=True, help_text=_("Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters") )
	algorithm = models.CharField( _('algorithm'), max_length=20, help_text=_("The algorithm used to hash passwords"), blank=True, null=True )
	salt = models.CharField( _('salt'), max_length=16, help_text=_("salt for the hash"), blank=True, null=True )
	hash = models.CharField( _('hash'), max_length=128, help_text=_("actual hash of the password"), blank=True, null=True )
	last_login = models.DateTimeField(_('last login'), default=datetime.datetime.now, auto_now=True)
	date_joined = models.DateTimeField(_('date joined'), default=datetime.datetime.now)

	def __init__( self, *args, **kwargs ):
		models.Model.__init__( self, *args, **kwargs )
		from RestAuthCommon import resource_validator

		if self.username and not resource_validator( self.username ):
			raise PreconditionFailed( "Username contains invalid characters" )

	def set_password( self, raw_password ):
		"""
		Set the password to the given value. Throws PasswordInvalid if
		the password is shorter than settings.MIN_PASSWORD_LENGTH.

		@raise PasswordInvalid: When the password is too short.
		"""
		if len( raw_password ) < settings.MIN_PASSWORD_LENGTH:
			raise PasswordInvalid( "Password too short" )

		self.algorithm = settings.HASH_ALGORITHM
		self.salt = get_salt()
		self.hash = get_hexdigest( self.algorithm, self.salt, raw_password )

	def set_unusable_password( self ):
		self.hash = None
		self.salt = None
		self.algorithm = None

	def check_password( self, raw_password ):
		"""
		Check the users password. If the current password hash is not
		of the same type as the current settings.HASH_ALGORITHM, the
		hash is updated but *not* saved.
		"""
		if not (self.algorithm and self.hash):
			return False
		
		digest = get_hexdigest( self.algorithm, self.salt, raw_password )
		if digest == self.hash: # correct
			if self.algorithm != settings.HASH_ALGORITHM: # pragma: no cover
				# we do this manually so we avoid any checks.
				self.algorithm = settings.HASH_ALGORITHM
				self.salt = get_salt()
				self.hash = get_hexdigest( self.algorithm, self.salt, raw_password )
			return True
		else: # password not correct
			return False

	def get_groups( self, service, recursive=True ):
		"""
		Get a list of groups that this user is a member of.

		@param service: Limit the list of groups to those defined by the
			given service.
		@type  service: service
		"""
		groups = set( self.group_set.filter( service=service ).only( 'name' ) )
		
		if not recursive: # pragma: no cover
			return groups
		
		# import here to avoid circular imports:
		from RestAuth.Groups.models import Group
		
		# next we get memberships derived from direct memberships:
		for group in groups.copy():
			inherited = group.get_inherited_memberships( service, groups )
			groups.update( inherited )
			
		# any remaining candidates
		exclude_ids = [ group.id for group in groups ]
		others = Group.objects.filter( service=service ).exclude( id__in=exclude_ids ).only( 'name' )
		for other in others:
			if other.is_indirect_member( self ):
				groups.add( other )
		return groups

	def add_property( self, key, value ):
		"""
		Add a new property to this user. It is an error if this property
		already exists.

		@raises PropertyExists: If the property already exists.
		@return: The property that was created
		"""
		from RestAuthCommon import resource_validator
		if not resource_validator( key ):
			raise PreconditionFailed( "Property contains invalid characters" )
			
		try:
			prop = Property( user=self, key=key, value=value )
			prop.save()
			return prop
		except IntegrityError:
			raise PropertyExists( key )		

	def get_properties( self ):
		dictionary = {}

		props = self.property_set.values_list( 'key', 'value' ).all()
		for key, value in props:
			dictionary[key] = value
		return dictionary

	def set_property( self, key, value ):
		"""
		Set the property identified by I{key} to I{value}. If the
		property already exists, it is overwritten.

		@return: Returns a tuple. The first value represents the 
			L{Property} acted upon and the second value is a string
			with the previous value or None if this was a new
			property.
		"""
		try:
			return self.add_property( key, value ), None
		except PropertyExists:
			# only update the right key.
			prop = self.property_set.get( key=key )
			old_value = prop.value
			prop.value = value
			prop.save()
			return prop, old_value

	def get_property( self, key ):
		"""
		Get value of a specific property.

		@raises Property.DoesNotExist: When the property does not exist.
		"""
		# exactly one SELECT statement
		return self.property_set.get( key=key )
	
	def del_property( self, key ):
		"""
		Delete a property.

		@raises Property.DoesNotExist: When the property does not exist.
		"""
		if self.property_set.filter( key=key ).exists():	
			self.property_set.filter( key=key ).delete()
		else:
			raise Property.DoesNotExist()

	def __unicode__( self ): # pragma: no cover
		return self.username

	def get_absolute_url( self ):
		return '/users/%s/'% urlquote( self.username )

class Property( models.Model ):
	user = models.ForeignKey( ServiceUser )
	key = models.CharField( max_length=128 )
	value = models.TextField()

	class Meta:
		unique_together = ( 'user', 'key' )

	def __unicode__( self ): # pragma: no cover
		return "%s: %s=%s"%(self.user.username, self.key, self.value)
	
	def get_absolute_url( self ):
		userpath = self.user.get_absolute_url()
		return '%sprops/%s/'%(userpath, urlquote( self.key ) )
