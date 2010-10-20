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

from django.db import models
from django.contrib.auth.models import User as Service
from RestAuth.Services.models import service_get
from RestAuth.Users.models import ServiceUser as User
from RestAuth.common.errors import ResourceExists
from django.utils.translation import ugettext_lazy as _

def group_get( name, service=None ):
	"""
	Get a group object from the name and service.

	@param name: Name of the new group
	@type  name: str
	@param service: The service this group should be associated to. If
		ommitted, the group will not be associated with any service.
	@type service: service
	"""
	return Group.objects.get( name=name, service=service )

def group_exists( name, service=None ):
	"""
	Check if a given service already exists.
	
	@param name: Name of the new group
	@type  name: str
	@param service: The service this group should be associated to. If
		ommitted, the group will not be associated with any service.
	@type service: service
	"""
	return Group.objects.filter( service=service, name=name ).exists()

def group_create( name, service=None ):
	"""
	Create a new group.

	@param name: Name of the new group
	@type  name: str
	@param service: The service this group should be associated to. If
		ommitted, the group will not be associated with any service.
	@type service: service
	"""
	if group_exists( name, service ):
		raise ResourceExists( 'Group "%s" already exists'%(name) )
	
	group = Group( name=name, service=service )
	group.save()
	return group

# Create your models here.
class Group( models.Model ):
	service = models.ForeignKey( Service, null=True,
		help_text=_("Service that is associated with this group.") )
	name = models.CharField(_('name'), max_length=30, 
		help_text=_("Required. Name of the group."))
	users = models.ManyToManyField( User )
	groups = models.ManyToManyField( 'self', symmetrical=False, related_name='parent_groups' )

	def get_members( self, recursive=True, lvl=0 ):
		users = set( self.users.all() )
		if recursive and lvl < 10:
			for gr in self.parent_groups.all():
				users = users.union( gr.get_members( recursive, lvl+1 ) )

		return users

	def is_member( self, user, recursive=True, lvl=0 ):
		if self.users.filter( username=user.username ).exists():
			return True

		if recursive and lvl < 10:
			return self.is_indirect_member( user, lvl+1 )
		return False

	def is_indirect_member( self, user, lvl=0 ):
		for group in self.parent_groups.all():
			if group.is_member( user, True, lvl ):
				return True
		return False

	def get_child_groups( self, lvl=0 ):
		"""
		Get a set of child groups.

		@param lvl: The recursion level. Used internally.
		@type  lvl: int
		@rtype: set
		@return: All direct and indirect child-groups of this group.
		"""
		child_groups = set( self.groups.all() )

		if lvl < 10:
			for group in self.groups.all():
				child_groups.union( group.get_child_groups( lvl+1 ) )

		return child_groups
