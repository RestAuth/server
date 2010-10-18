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
from optparse import OptionParser, OptionGroup, IndentedHelpFormatter

# parse arguments
usage = "%prog [options] [action] [action parameters]"
desc = """%prog manages services in RestAuth. Services are websites, hosts, etc.
that use RestAuth as authentication service. Valid actions are help, add, remove,
view, list and set-hosts."""
prog = os.path.basename(sys.argv[0])
epilog = """Use %s help <action> to get help for each action and their
parameters.""" % (prog)
parser = OptionParser( usage=usage, description=desc, epilog=epilog)
parser.add_option( '--settings', default='RestAuth.settings',
	help="The path to the Django settings module (Usually the default is fine)." )
group = OptionGroup( parser, 'Options for action "add"' )
group.add_option( '--password', dest="pwd", 
	help="Password of the service. If not provided, you will be prompted." )
parser.add_option_group( group )
options, args = parser.parse_args()

# Setup environment
os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
if 'RESTAUTH_PATH' in os.environ:
	sys.path.append( os.environ['RESTAUTH_PATH'] )

# error-handling arguments
if not args:
	sys.stderr.write( "Please provide an action." )
	sys.exit(1)
if args[0] != 'help':
	# we don't need this for help
	try:
		from RestAuth.BasicAuth.models import *
	except ImportError:
		sys.stderr.write( 'Error: Cannot import RestAuth. Please make sure your RESTAUTH_PATH environment variable is set correctly.\n' )
		sys.exit(1)

if args[0] == 'add':
	if not options.pwd:
		import getpass
		options.pwd = getpass.getpass( 'password: ' )
		confirm = getpass.getpass( 'confirm: ' )

		while options.pwd != confirm:
			print( "Passwords do not match, please try again!" )
			options.pwd = getpass.getpass( 'password: ' )
			confirm = getpass.getpass( 'confirm: ' )

	try:
		service_create( args[1], options.pwd, args[2:] )
	except ServiceAlreadyExists:
		print( "Error: Service already exists." )
		sys.exit(1)
elif args[0] == 'remove' or args[0] == 'rm':
	service_delete( args[1] )
elif args[0] == 'list':
	for service in Service.objects.all():
		print( service.username )
elif args[0] == 'view':
	service = service_get( args[1] )
	print( service.username )
	print( 'Last used: %s'%(service.last_login) )
	hosts = service.addresses.all()
	print( 'Hosts: %s'%(', '.join( [ host.address for host in hosts ] ) ) )
elif args[0] == 'set-hosts':
	service = service_get( args[1] )
	service.set_hosts( args[2:] )
elif args[0] == 'help':
	if len(args) > 1:
		usage = '%prog [options] ' + args[1] + ' '
		help_parser = OptionParser(usage=usage, add_help_option=False )
		help_parser.add_option( parser.get_option( '--settings' ) )
		
		if args[1] == 'add':
			help_parser.usage += '<service> [host]...'
			desc = """Add <service> to RestAuth. You can give one or
more hosts that the new service is able to connect from. If ommitted, the
service can't connect from any host and is thus unusable."""
			opt = parser.get_option( '--password' )
			help_parser.add_option( opt )
		elif args[1] == 'remove':
			help_parser.usage += '<service>'
			desc = 'Remove a service that no longer uses RestAuth.'
		elif args[1] == 'list':
			desc = 'List all services known to RestAuth.'
		elif args[1] == 'view':
			help_parser.usage += '<service>'
			desc = 'View details on <service>.'
		elif args[1] == 'set-hosts':
			help_parser.usage += '<service> [host]...'
			desc = """The given service is allowed to connect from
the given hosts. Naming no hosts effectively disables the service."""
		else:
			print('Unknown action.')
			sys.exit(1)
		help_parser.description = desc
		help_parser.print_help()
	else:
		parser.print_help()
else:
	print( 'unknown action' )
