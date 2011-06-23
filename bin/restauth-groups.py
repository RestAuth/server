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
from optparse import OptionParser, OptionGroup
from operator import attrgetter

# parse arguments
usage = "%prog [options] [action] [action parameters]"
desc = """%prog manages groups in RestAuth. Groups can have users and groups as
members, handing down users to member groups. For a group to be visible to a
service, it must be associated with it. It is possible for a group to not be
associated with any service, which is usefull for e.g. a group containing global
super-users. Valid actions are help, add, list, view, add-user, add-group,
remove, remove-user, and remove-group."""
prog = os.path.basename(sys.argv[0])
epilog = """Use %s help <action> to get help for each action and their
parameters.""" % (prog)
parser = OptionParser( usage=usage, description=desc, epilog=epilog)
parser.add_option( '--settings', default='RestAuth.settings',
	help="The path to the Django settings module (Usually the default is fine)." )
parser.add_option( '--service', help="""Assume that the named group is from
SERVICE. If ommitted, the group is assumed to not be associated with any
service.""" )

group = OptionGroup( parser, 'Options for action add-group and remove-group' )
group.add_option( '--child-service', metavar='SERVICE', help="""Assume that the
named childgroup is from SERVICE. If ommitted, %s will throw an error if the
group is defined by multiple services."""%(prog) )
parser.add_option_group( group )

options, args = parser.parse_args()

# Setup environment
os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
if 'RESTAUTH_PATH' in os.environ:
	sys.path.append( os.environ['RESTAUTH_PATH'] )
sys.path.append( os.getcwd() )

# error-handling arguments
if not args:
	sys.stderr.write( "Please provide an action.\n" )
	sys.exit(1)
if args[0] != 'help':
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
		none_names = [ service.name for service in servs[None] ]
		none_names.sort()
		print( '%sNone: %s'%(indent, ', '.join( none_names ) ) )
		del servs[None]
	
	service_names = sorted( servs.keys(), key=attrgetter('username') )
	
	for name in service_names:
		names = [ service.name for service in servs[name] ]
		names.sort()
		print( '%s%s: %s'%(indent, name, ', '.join(names) ) )

if args[0] in [ 'create', 'add' ]:
	if options.service:
		service = Service.objects.get( username=options.service )
		group_create( args[1].decode( 'utf-8' ), service )
	else:
		group_create( args[1].decode( 'utf-8' ) )
elif args[0] in [ 'list', 'ls' ]:
	if options.service == 'ALL':
		print_groups_by_service( groups = Group.objects.all() )
		
	else:
		qs = Group.objects.values_list( 'name', flat=True ).order_by( 'name' )
		if options.service:
			groups = qs.filter( service__username=options.service )
		else:
			groups = qs.filter( service=None )
		for group in groups:
			print( group )
elif args[0] == 'view':
	if options.service:
		group = group_get( args[1], Service.objects.get( username=options.service ) )
	else:
		group = group_get( args[1] )

	explicit_users = [ user.username for user in group.get_members( False ) ]
	effective_users = [ user.username for user in group.get_members() ]
	parent_groups = list( group.parent_groups.all() )
	child_groups = list( group.groups.all() )
	if explicit_users:
		explicit_users.sort()
		print( '* Explicit members: %s'%( ', '.join( explicit_users ) ) )
	else:
		print( '* No explicit members' )
	if effective_users:
		effective_users.sort()
		print( '* Effective members: %s'%( ', '.join( effective_users ) ) )
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
elif args[0] == 'add-user':
	if options.service:
		group = group_get( args[1], Service.objects.get( username=options.service ) )
	else:
		group = group_get( args[1] )

	user = user_get( args[2] )
	
	group.users.add( user )
	group.save()
elif args[0] == 'add-group':
	if options.service:
		group = group_get( args[1], Service.objects.get( username=options.service ) )
	else:
		group = group_get( args[1] )
	if options.child_service:
		child_service = Service.objects.get( username=options.cild_service )
		child_group = group_get( args[2], child_service )
	else:
		child_group = group_get( args[2] )

	group.groups.add( child_group )
	group.save()
elif args[0] in [ 'delete', 'del', 'rm' ]:
	if options.service:
		group = group_get( args[1], Service.objects.get( username=options.service ) )
	else:
		group = group_get( args[1] )

	group.delete()
elif args[0] in [ 'remove-user', 'rm-user', 'del-user' ]:
	if options.service:
		group = group_get( args[1], Service.objects.get( username=options.service ) )
	else:
		group = group_get( args[1] )

	user = user_get( args[2] )
	if user in group.users.all():
		group.users.remove( user )
		group.save()
elif args[0] in [ 'remove-group', 'rm-group', 'del-group' ]:
	if options.service:
		group = group_get( args[1], Service.objects.get( username=options.service ) )
	else:
		group = group_get( args[1] )
	if options.child_service:
		child_service = Service.objects.get( username=options.cild_service )
		child_group = group_get( args[2], child_service )
	else:
		child_group = group_get( args[2] )

	if child_group in group.groups.all():
		group.groups.remove( child_group )
		group.save()
elif args[0] == 'help':
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
