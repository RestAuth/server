#!/usr/bin/env python
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

import os, sys, getpass

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
	os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
sys.path.append( os.getcwd() )

try:
	from RestAuth.Services.models import *
	from RestAuth.common.cli import pwd_parser, service_parser
except ImportError:
	sys.stderr.write( 'Error: Cannot import RestAuth. Please make sure RestAuth is in your PYTHONPATH.\n' )
	sys.exit(1)

args = service_parser.parse_args()

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