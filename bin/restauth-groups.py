#!/usr/bin/env python
#
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

import os, sys
from argparse import ArgumentParser
from operator import attrgetter

# parse arguments
desc = """%(prog)s manages groups in RestAuth. Groups can have users and groups as members, handing
down users to member groups. For a group to be visible to a service, it must be associated with it.
It is possible for a group to not be associated with any service, which is usefull for e.g. a group
containing global super-users. Valid actions are help, add, list, view, add-user, add-group, remove,
remove-user, and remove-group."""
parser = ArgumentParser( description=desc )
parser.add_argument( '--service', help="""Act as if %(prog)s was the service named SERVICE. If
	ommitted, %(prog)s acts on groups that are not associated with any service.""" )

group_p = ArgumentParser(add_help=False)
group_p.add_argument( 'group', help="The name of the group." )

subparsers = parser.add_subparsers( title="Available actions", dest='action',
	description="""Use '%(prog)s action --help' for more help on each action.""" )
subparsers.add_parser( 'add', help="Add a new group.", parents=[group_p],
	description="Add a new group." )
subparsers.add_parser( 'list', help="List all groups.", description="List all groups." )
subparsers.add_parser( 'view', help="View details of a group.", parents=[group_p],
	description="View details of a group." )

add_user_p = subparsers.add_parser( 'add-user', parents=[group_p], help="Add a user to a group.",
	description="Add a user to a group." )
add_user_p.add_argument( 'user', help="The name of the user.")

add_group_p = subparsers.add_parser( 'add-group', parents=[group_p], help="""Make a group a subgroup
		to another group.""",
	description="""Make a group a subgroup of another group. The subgroup will inherit all
		memberships from the parent group.""" )
add_group_p.add_argument( 'subgroup', help="The name of the subgroup.")
add_group_p.add_argument( '--child-service', metavar='SERVICE', help="""Assume that the named
	subgroup is from SERVICE.""")

add_user_p = subparsers.add_parser( 'rm-user', parents=[group_p],
	help="Remove a user from a group.",
	description="Remove a user from a group." )
add_user_p.add_argument( 'user', help="The name of the user.")

add_user_p = subparsers.add_parser( 'rm-group', parents=[group_p], help="""Remove a subgroup from
		a group.""",
	description="""Remove a subgroup from a group. The subgroup will no longer inherit all
		memberships from a parent group.""" )
add_user_p.add_argument( 'subgroup', help="The name of the subgroup.")

add_user_p = subparsers.add_parser( 'rm', parents=[group_p],
	help="Remove a group.",
	description="Remove a group." )

args = parser.parse_args()

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
	os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
if 'RESTAUTH_PATH' in os.environ:
	sys.path.append( os.environ['RESTAUTH_PATH'] )
sys.path.append( os.getcwd() )

# we don't need this for help
try:
	from RestAuth.Groups.models import Group, group_get, group_create
	from RestAuth.Users.models import ServiceUser, user_get
	from RestAuth.Services.models import Service
except ImportError:
	sys.stderr.write( 'Error: Cannot import RestAuth. Please make sure your RESTAUTH_PATH environment variable is set correctly.\n' )
	sys.exit(1)

def print_groups_by_service( groups, indent='' ):
	servs = {}
	for group in groups:
		if servs.has_key( group.service ):
			servs[group.service].append( group )
		else:
			servs[group.service] = [ group ]

	if None in servs:
		none_names = [ service.name.encode('utf-8') for service in servs[None] ]
		none_names.sort()
		print( '%sNone: %s'%(indent, ', '.join( none_names ) ) )
		del servs[None]
	
	service_names = sorted( servs.keys(), key=attrgetter('username') )
	
	for name in service_names:
		names = [ service.name.encode('utf-8') for service in servs[name] ]
		names.sort()
		print( '%s%s: %s'%(indent, name, ', '.join(names) ) )

if args.action in [ 'create', 'add' ]:
	if args.service:
		service = Service.objects.get( username=args.service )
		group_create( args.group.decode( 'utf-8' ), service )
	else:
		group_create( args.group.decode( 'utf-8' ) )
elif args.action in [ 'list', 'ls' ]:
	qs = Group.objects.values_list( 'name', flat=True ).order_by( 'name' )
	if args.service:
		groups = qs.filter( service__username=args.service )
	else:
		groups = qs.filter( service=None )
	for group in groups:
		print( group.encode( 'utf-8' ) )
elif args.action == 'view':
	try:
		if args.service:
			group = group_get( args.group, Service.objects.get( username=args.service ) )
		else:
			group = group_get( args.group )
	except Group.DoesNotExist:
		print( 'Error: %s: Group does not exist'%args.group )
		sys.exit( 1 )

	explicit_users = group.get_members( False )
	effective_users = group.get_members()
	parent_groups = list( group.parent_groups.all() )
	child_groups = list( group.groups.all() )
	if explicit_users:
		print( '* Explicit members: %s'%( ', '.join( sorted(explicit_users) ) ) )
	else:
		print( '* No explicit members' )
	if effective_users:
		print( '* Effective members: %s'%( ', '.join( sorted(effective_users) ) ) )
	else:
		print( '* No effective members' )
	if parent_groups:
		print( '* Parent groups:' )
		print_groups_by_service( parent_groups, '    ' )
	else:
		print( '* No parent groups' )
	if child_groups:
		print( '* Child groups:' )
		print_groups_by_service( child_groups, '    ' )
	else:
		print( '* No child groups' )
elif args.action == 'add-user':
	try:
		if args.service:
			group = group_get( args.group, Service.objects.get( username=args.service ) )
		else:
			group = group_get( args.group )
	except Group.DoesNotExist:
		print( 'Error: %s: Group does not exist'%args.group )
		sys.exit( 1 )

	user = user_get( args.user )
	
	group.users.add( user )
	group.save()
elif args.action == 'add-group':
	try:
		if args.service:
			group = group_get( args.group, Service.objects.get( username=args.service ) )
		else:
			group = group_get( args.group )
	except Group.DoesNotExist:
		print( 'Error: %s: Group does not exist'%args.group )
		sys.exit( 1 )
	if args.child_service:
		child_service = Service.objects.get( username=args.child_service )
		child_group = group_get( args.subgroup, child_service )
	else:
		child_group = group_get( args.subgroup )

	group.groups.add( child_group )
	group.save()
elif args.action in [ 'delete', 'del', 'rm' ]:
	try:
		if args.service:
			group = group_get( args.group, Service.objects.get( username=args.service ) )
		else:
			group = group_get( args.group )
	except Group.DoesNotExist:
		print( 'Error: %s: Group does not exist'%args.group )
		sys.exit( 1 )

	group.delete()
elif args.action in [ 'remove-user', 'rm-user', 'del-user' ]:
	try:
		if args.service:
			group = group_get( args.group, Service.objects.get( username=args.service ) )
		else:
			group = group_get( args.group )
	except Group.DoesNotExist:
		print( 'Error: %s: Group does not exist'%args.group )
		sys.exit( 1 )

	user = user_get( args.user )
	if user in group.users.all():
		group.users.remove( user )
		group.save()
elif args.action in [ 'remove-group', 'rm-group', 'del-group' ]:
	try:
		if args.service:
			group = group_get( args.group, Service.objects.get( username=args.service ) )
		else:
			group = group_get( args.group )
	except Group.DoesNotExist:
		print( 'Error: %s: Group does not exist'%args.group )
		sys.exit( 1 )
	
	try:
		if args.child_service:
			child_service = Service.objects.get( username=args.child_service )
			child_group = group_get( args.subgroup, child_service )
		else:
			child_group = group_get( args.subgroup )
	except Group.DoesNotExist:
		print( 'Error: %s: Does not exist'%args.subgroup )
		sys.exit( 1 )

	if child_group in group.groups.all():
		group.groups.remove( child_group )
		group.save()
elif args.action == 'help':
	if len( args ) > 1:
		help_parser = OptionParser(usage='%prog [options] ',
			add_help_option=False )
		help_parser.add_option( '--settings', default='RestAuth.settings',
			help="The path to the Django settings module (Usually the default is fine)." )
		if args[1] == 'create':
			help_parser.usage += 'add <group>'
			desc = """Create a group with the name <group>."""
			help_parser.add_option( '--service', help="""Associate the
new group with SERVICE. If ommitted, the group will not be associated with any
service.""" )
		elif args[1] == 'list':
			help_parser.usage += 'list'
			desc = """Print a list of groups known to RestAuth."""
			help_parser.add_option( '--service', help="""Only list the
groups associated with SERVICE. If ommitted, only list groups not associated
with any service. To list all groups, set SERVICE to "ALL" (without quotes).""" )
		elif args[1] == 'view':
			help_parser.usage += 'view <group>'
			desc = """Show details of <group>"""
			opt = parser.get_option( '--service' )
			help_parser.add_option( opt )
		elif args[1] == 'add-user':
			help_parser.usage += 'add-user <group> <user>'
			desc = """Add <user> to <group>."""
			opt = parser.get_option( '--service' )
			help_parser.add_option( opt )
		elif args[1] == 'add-group':
			help_parser.usage += 'add-group <group> <child-group>'
			desc = """Add <child-group> to the <group>. This has the
effect that all members of <group> are implicitly also member of <child-group>.
Note that the two groups do not have to be associated with the same service."""
			opt = parser.get_option( '--service' )
			help_parser.add_option( opt )
			opt = parser.get_option( '--child-service' )
			help_parser.add_option( opt )
		elif args[1] == 'delete':
			help_parser.usage += 'delete <group>'
			desc = """Delete <group>."""
			opt = parser.get_option( '--service' )
			help_parser.add_option( opt )
		elif args[1] == 'remove-user':
			help_parser.usage += 'remove-user <group> <user>'
			desc = 'Remove <user> from <group>.'
			opt = parser.get_option( '--service' )
			help_parser.add_option( opt )
		elif args[1] == 'remove-group':
			help_parser.usage += 'remove-group <group> <childgroup>'
			desc = 'Remove <childgroup> from <group>.'
			opt = parser.get_option( '--service' )
			help_parser.add_option( opt )
			opt = parser.get_option( '--child-service' )
			help_parser.add_option( opt )
		else:
			print( "Unknown action." )
			sys.exit(1)
		help_parser.description = desc
		help_parser.print_help()
	else:
		parser.print_help()

	pass
else:
	print( "Unknown action." )
	sys.exit(1)
