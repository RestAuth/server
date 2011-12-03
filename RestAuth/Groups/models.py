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

from django.db import models
from django.db.utils import IntegrityError

from django.contrib.auth.models import User as Service
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlquote

from RestAuth.Users.models import ServiceUser as User
from RestAuth.common.errors import GroupExists
from RestAuthCommon.error import PreconditionFailed

def group_create( name, service=None ):
	"""
	Create a new group.

	@param name: Name of the new group
	@type  name: str
	@param service: The service this group should be associated to. If
		ommitted, the group will not be associated with any service.
	@type service: service
	"""
	try:
		return Group.objects.create(name=name, service=service)
	except IntegrityError:
		raise GroupExists('Group "%s" already exists' % name)

# Create your models here.
class Group( models.Model ):
	service = models.ForeignKey( Service, null=True,
		help_text=_("Service that is associated with this group.") )
	name = models.CharField(_('name'), max_length=30, db_index=True, 
		help_text=_("Required. Name of the group."))
	users = models.ManyToManyField(User)
	groups = models.ManyToManyField( 'self', symmetrical=False, related_name='parent_groups' )
	
	class Meta:
		unique_together = ('name', 'service')
	
	def __init__( self, *args, **kwargs ):
		models.Model.__init__( self, *args, **kwargs )
		from RestAuthCommon import resource_validator

		if self.name and not resource_validator( self.name ):
			raise PreconditionFailed( "Name of group contains invalid characters" )

	def get_members( self, recursive=True, lvl=0 ):
		users = set( self.users.values_list( 'username', flat=True ) )
		
		if recursive and lvl < 10:
			for parent in self.parent_groups.only( 'name' ):
				users = users.union( parent.get_members( recursive, lvl+1 ) )

		return users

	def is_member( self, user, recursive=True, lvl=0 ):
		if self.users.filter( id=user.id ).exists():
			return True

		if recursive and lvl < 10:
			for parent in self.parent_groups.only( 'name' ):
				if parent.is_member( user, recursive, lvl+1 ):
					return True
		return False

	def is_indirect_member(self, user):
		for parent in self.parent_groups.only( 'name' ):
			if parent.is_member( user, True ):
				return True
		return False
	
	def save(self, *args, **kwargs):
		if self.service == None:
			conflict = Group.objects.filter(name=self.name, service=None)
			if self.id:
				conflict.exclude(pk=self.id)
			if conflict.exists():
				raise IntegrityError("columns name, service_id are not unique")
		super(Group, self).save(*args, **kwargs)
	
	def __unicode__( self ): # pragma: no cover
		if self.service:
			return "%s/%s"%( self.name, self.service.username )
		else:
			return "%s/None"%(self.name)
			
	def get_absolute_url( self ):
		return '/groups/%s/'%  urlquote(self.name)
