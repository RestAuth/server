from django.db import models
from django.contrib.auth.models import User as Project
from RestAuth.Users.models import ServiceUser as User
from RestAuth.common import *
from django.utils.translation import ugettext_lazy as _

def group_get( name, service=None ):
	"""
	@raises ResourceNotFound: If no group with the given name exists.
	"""
	try:
		if service:
			return Group.objects.get( service=service, name=name )
		else:
			return Group.objects.get( name=name )
	except Group.MultipleObjectsReturned:
		raise ResourceNotFound( 'The group "%s" is defined in multiple services'%(name) )
	except Group.DoesNotExist:
		raise ResourceNotFound( 'Group "%s" not found'%(name) )

def group_exists( service, name ):
	return Group.objects.filter( service=service, name=name ).exists()

def group_create( service, name ):
	if group_exists( service, name ):
		raise ResourceExists( 'Group "%s" already exists'%(name) )
	else:
		group = Group( service=service, name=name )
		group.save()

# Create your models here.
class Group( models.Model ):
	service = models.ForeignKey( Project, 
		help_text=_("Service that is associated with this group.") )
	name = models.CharField(_('name'), max_length=30, 
		help_text=_("Required. Name of the group."))
	users = models.ManyToManyField( User )
	groups = models.ManyToManyField( 'self', symmetrical=False, related_name='parent_groups' )

	def get_members( self, recursive=True, lvl=0 ):
		users = set( self.users.all() )
		if recursive and lvl < 10:
			print( 'recursive...' )
			for gr in self.parent_groups.all():
				print( gr.name )
				users = users.union( gr.get_members( recursive, lvl+1 ) )

		print( '%s: %s'%(self.name, ', '.join( [ user.username for user in users ] ) ) )
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
