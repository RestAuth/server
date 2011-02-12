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

import os, sys, getpass
from optparse import OptionParser, OptionGroup, IndentedHelpFormatter

# parse arguments
usage = "%prog [options] [action] [action parameters]"
desc = """%prog manages services in RestAuth. Services are websites, hosts, etc.
that use RestAuth as authentication service. Valid actions are help, add, remove,
view, list, set-hosts and set-password."""
prog = os.path.basename(sys.argv[0])
epilog = """Use %s help <action> to get help for each action and their
parameters.""" % (prog)
parser = OptionParser( usage=usage, description=desc, epilog=epilog)
parser.add_option( '--settings', default='RestAuth.settings',
	help="The path to the Django settings module (Usually the default is fine)." )
group = OptionGroup( parser, 'Options for actions add/set-password' )
group.add_option( '--password', dest="pwd", 
	help="Password of the service. If not provided, you will be prompted." )
parser.add_option_group( group )
options, args = parser.parse_args()

# Setup environment
os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
if 'RESTAUTH_PATH' in os.environ:
	sys.path.append( os.environ['RESTAUTH_PATH'] )
sys.path.append( os.getcwd() )

# error-handling arguments
if not args:
	sys.stderr.write( "Please provide an action." )
	sys.exit(1)

if args[0] != 'help':
	# we don't need this for help
	try:
		from RestAuth.Services.models import *
	except ImportError:
		print( sys.path )
		sys.stderr.write( 'Error: Cannot import RestAuth. Please make sure your RESTAUTH_PATH environment variable is set correctly.\n' )
		sys.exit(1)

def get_password( options ):
	if options.pwd:
		return options.pwd

	password = getpass.getpass( 'password: ' )
	confirm = getpass.getpass( 'confirm: ' )
	if password != confirm:
		print( "Passwords do not match, please try again." )
		return get_password( options )
	else:
		return password

if args[0] in [ 'create', 'add']:
	if len( args ) < 2:
		print( "Please name a service to add." )
		sys.exit(1)

	try:
		check_service_username( args[1] )
		service = Service( username=args[1] )
		service.save()
		service.set_password( get_password( options ) )
		service.set_hosts( args[2:] )
		service.save()
	except IntegrityError as e:
		print( "Error: %s: Service already exists."%args[1] )
		sys.exit(1)
	except ServiceUsernameNotValid as e:
		print( e )
		sys.exit(1)
elif args[0] in [ 'remove', 'rm', 'del', 'delete' ]:
	if len( args ) < 2:
		print( "Please name a service to remove." )
		sys.exit(1)
	elif len( args ) > 2:
		print( "Please name exactly one service to remove." )
		sys.exit(1)

	try:
		service_delete( args[1] )
	except ServiceNotFound:
		print( "Error: %s: Service not found."%args[1] )
		sys.exit(1)
elif args[0] in [ 'list', 'ls' ]:
	for service in Service.objects.all():
		hosts = [ str(host.address) for host in service.hosts.all() ]
		print( '%s: %s'%(service.username, ', '.join(hosts)) )
elif args[0] == 'view':
	if len( args ) < 2:
		print( "Please name a service to view. Try 'list' for a list of services." )
		sys.exit(1)
	elif len( args ) > 2:
		print( "Please name exactly one service to remove." )
		sys.exit(1)

	try:
		service = service_get( args[1] )
		print( service.username )
		print( 'Last used: %s'%(service.last_login) )
		hosts = [ str(host.address) for host in service.hosts.all() ]
		print( 'Hosts: %s'%(', '.join( hosts )) )
	except ServiceNotFound:
		print( "Error: %s: Service not found."%args[1] )
		sys.exit(1) 
elif args[0] == 'set-hosts':
	if len( args ) < 2:
		print( "Please name a service to set hosts for." )
		sys.exit(1)

	try:
		service = service_get( args[1] )
		service.set_hosts( args[2:] )
	except ServiceNotFound:
		print( "Error: %s: Service not found."%args[1] )
		sys.exit(1)
elif args[0] == 'set-password':
	try:
		service = service_get( args[1] )
		service.set_password( get_password( options ) )
		service.save()
	except ServiceNotFound:
		print( "Error: %s: Service not found."%args[1] )
		sys.exit(1) 
elif args[0] == 'help':
	if len(args) > 1:
		usage = '%prog [options] ' + args[1] + ' '
		help_parser = OptionParser(usage=usage, add_help_option=False )
		help_parser.add_option( parser.get_option( '--settings' ) )
		
		if args[1] == 'add':
			help_parser.usage += '<service> [host]...'
			desc = """Add a service to RestAuth. The service can
contain any ASCII character except a double colon (':'). You can give one or
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
			desc = 'View details on a service.'
		elif args[1] == 'set-hosts':
			help_parser.usage += '<service> [host]...'
			desc = """Set the hosts that a service is allowed to
connect from. Naming no hosts effectively disables the service."""
		elif args[1] == 'set-password':
			help_parser.usage += '<service>'
			desc = """Set the password for the given service."""
			opt = parser.get_option( '--password' )
			help_parser.add_option( opt )
		else:
			print('Unknown action.')
			sys.exit(1)
		help_parser.description = desc
		help_parser.print_help()
	else:
		parser.print_help()
else:
	print( 'unknown action' )
