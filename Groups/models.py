from django.db import models
from django.contrib.auth.models import User as Project
from RestAuth.Users.models import ServiceUser as User
from RestAuth.common import *
from django.utils.translation import ugettext_lazy as _

def group_get( project, name ):
	try:
		return Group.objects.get( project=project, name=name )
	except Group.DoesNotExist:
		raise ResourceNotFound()

def group_exists( project, name ):
	return Group.objects.filter( project=project, name=name ).exists()

def group_create( project, name ):
	if group_exists( project, name ):
		raise ResourceExists( 'group not found' )
	else:
		group = Group( project=project, name=name )
		group.save()

# Create your models here.
class Group( models.Model ):
	project = models.ForeignKey( Project, help_text=_("Required. Associated project") )
	name = models.CharField(_('name'), max_length=30, help_text=_("Required. Name of the group."))
	users = models.ManyToManyField( User )
	groups = models.ManyToManyField( 'self' )

	def get_members( self, recursive=True, lvl=0 ):
		users = self.users.all()
		if recursive and lvl < 10:
			for gr in self.groups.all():
				users += gr.get_members( recursive, lvl+1 )

		return users

	def is_member( self, user, recursive=True, lvl=0 ):
		if user in self.users:
			return True

		if recursive and lvl < 10:
			return self.is_indirect_member( user, lvl+1 )
		return False

	def is_indirect_member( self, user, lvl=0 ):
		for group in self.groups.all():
			if group.is_member( user, True, lvl ):
				return True
		return False
