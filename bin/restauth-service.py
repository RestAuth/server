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

import os, sys, getpass, random, string
from argparse import ArgumentParser, Action

class PasswordGenerator( Action ):
	def __call__( self, parser, namespace, values, option_string ):
		passwd = ''.join( random.choice( string.printable ) for x in range(30) )
		print( passwd )
		setattr( namespace, self.dest, passwd )

# parse arguments
desc = """%(progs manages services in RestAuth. Services are websites, hosts, etc. that use RestAuth
as authentication service."""
parser = ArgumentParser( description=desc )

service_p = ArgumentParser(add_help=False)
service_p.add_argument( 'service', help="The name of the service." )

pwd_p = ArgumentParser( add_help=False )
pwd_group = pwd_p.add_mutually_exclusive_group()
pwd_group.add_argument( '--password', dest='pwd', metavar='PWD', help="Password for the service." )
pwd_group.add_argument( '--gen-password', action=PasswordGenerator, nargs=0, dest='pwd',
	help="Generate password for the service and print it to stdout." )

host_p = ArgumentParser( add_help=False )
host_p.add_argument( 'hosts', metavar='host', nargs='*', help="""A host that the service is able to
	connect from. You can name multiple hosts as additional positional arguments. If ommitted,
	this service cannot be used from anywhere.""")

subparsers = parser.add_subparsers( title="Available actions", dest='action',
	description="""Use '%(prog)s action --help' for more help on each action.""" )

add_p = subparsers.add_parser( 'add', help="Add a new service.", parents=[service_p, host_p],
	description="Add a new service." )

subparsers.add_parser( 'ls', help="List all services.",
	description="""List all available services.""")
subparsers.add_parser( 'rm', help="Remove a service.", parents=[service_p],
	description="""Completely remove a service. This will also remove any groups associated with
		that service.""" )
subparsers.add_parser( 'view', help="View details of a service.", parents=[service_p],
	description="View details of a service." )
subparsers.add_parser( 'view', help="View details of a service.", parents=[service_p],
	description="View details of a service." )

subparsers.add_parser( 'set-hosts', parents=[service_p, host_p],
	help="Set hosts that a service can connect from.",
	description="Set hosts that a service can connect from." )
subparsers.add_parser( 'set-password', parents=[service_p, pwd_p],
	help="Set the password for a service.", description="Set the password for a service." )

args = parser.parse_args()

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
	os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
if 'RESTAUTH_PATH' in os.environ:
	sys.path.append( os.environ['RESTAUTH_PATH'] )
sys.path.append( os.getcwd() )

try:
	from RestAuth.Services.models import *
except ImportError:
	sys.stderr.write( 'Error: Cannot import RestAuth. Please make sure your RESTAUTH_PATH environment variable is set correctly.\n' )
	sys.exit(1)

def get_password( args ):
	if args.pwd:
		return args.pwd

	password = getpass.getpass( 'password: ' )
	confirm = getpass.getpass( 'confirm: ' )
	if password != confirm:
		print( "Passwords do not match, please try again." )
		return get_password( args )
	else:
		return password

if args.action in [ 'create', 'add']:
	try:
		check_service_username( args.service )
		service = Service( username=args.service )
		service.save()
		service.set_password( get_password( args ) )
		service.set_hosts( args.hosts )
		service.save()
	except IntegrityError as e:
		print( "Error: %s: Service already exists."%args.service )
		sys.exit(1)
	except ServiceUsernameNotValid as e:
		print( e )
		sys.exit(1)
elif args.action in [ 'remove', 'rm', 'del', 'delete' ]:
	try:
		service_delete( args.service )
	except Service.DoesNotExist:
		print( "Error: %s: Service not found."%args.service )
		sys.exit(1)
elif args.action in [ 'list', 'ls' ]:
	for service in Service.objects.all():
		hosts = [ str(host.address) for host in service.hosts.all() ]
		print( '%s: %s'%(service.username, ', '.join(hosts)) )
elif args.action == 'view':
	try:
		service = Service.objects.get( username=args.service )
		print( service.username )
		print( 'Last used: %s'%(service.last_login) )
		hosts = [ str(host.address) for host in service.hosts.all() ]
		print( 'Hosts: %s'%(', '.join( hosts )) )
	except Service.DoesNotExist:
		print( "Error: %s: Service not found."%args.service )
		sys.exit(1) 
elif args.action == 'set-hosts':
	try:
		service = Service.objects.get( username=args.service )
		service.set_hosts( args.hosts )
	except Service.DoesNotExist:
		print( "Error: %s: Service not found."%args.service )
		sys.exit(1)
elif args.action == 'set-password':
	try:
		service = Service.objects.get( username=args.service )
		service.set_password( get_password( args ) )
		service.save()
	except Service.DoesNotExist:
		print( "Error: %s: Service not found."%args.service )
		sys.exit(1) 