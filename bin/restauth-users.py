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
from argparse import ArgumentParser

# parse arguments
desc = """Manages users in RestAuth. Users are clients that want to authenticate with services that
	use RestAuth."""
parser = ArgumentParser( description=desc )

username_p = ArgumentParser(add_help=False)
username_p.add_argument( 'username', help="The name of the user." )

pwd_p = ArgumentParser( add_help=False )
pwd_p.add_argument( '--password', '-p', metavar='PWD', dest='pwd',
	help="""Use PWD for the users password. If not given, you will be prompted.""" )

subparsers = parser.add_subparsers( title="Available actions", dest='action',
	description="""Use '%(prog)s action --help' for more help on each action.""" )
subparsers.add_parser( 'add', help="Add a new user.", parents=[username_p, pwd_p],
		      description="Add a new user." )
subparsers.add_parser( 'list', help="List all users.", description="List all users." )
subparsers.add_parser( 'verify', help="Verify a users password.", parents=[username_p, pwd_p],
		      description="Verify the password of a user." ) 
subparsers.add_parser( 'passwd', help="Set the password of a user.", parents=[username_p, pwd_p],
		      description="Set the password of a user." )
subparsers.add_parser( 'rm', help="Remove a user.", parents=[username_p],
		      description="Remove a user." )

view_p = subparsers.add_parser( 'view', help="View details of a user.", parents=[username_p ] )
view_p.add_argument( '--service', help="View the information as SERVICE would see it. (optional)." )

args = parser.parse_args()

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
	os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
if 'RESTAUTH_PATH' in os.environ:
	sys.path.append( os.environ['RESTAUTH_PATH'] )
sys.path.append( os.getcwd() )

try:
	from RestAuth.Users.models import ServiceUser, user_get, validate_username
	from RestAuth.Services.models import Service
	from RestAuth.common import errors
	from django.db.utils import IntegrityError
except ImportError:
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

if args.action in ['create', 'add']:
	username = args.username.decode( 'utf-8')

	try:
		validate_username( username )
		user = ServiceUser( username=username )
		password = get_password( args )
		user.set_password( password )
		user.save()
	except IntegrityError as e:
		print( "Error: %s: User already exists."%args.username )
		sys.exit(1)
	except errors.PreconditionFailed as e:
		print( "Error: %s"%e )
		sys.exit(1)
elif args.action in ['ls', 'list']:
	for user in ServiceUser.objects.values_list( 'username', flat=True ):
		print( user.encode('utf-8' ) )
elif args.action == 'verify':
	try:
		user = user_get( args.username )
		if not args.pwd:
			args.pwd = getpass.getpass( 'password: ' )
		if user.check_password( args.pwd ):
			print( 'Ok.' )
		else:
			print( 'Failed.' )
			sys.exit(1)
	except ServiceUser.DoesNotExist:
		print( "Error: %s: User does not exist."%args.username )
		sys.exit(1)
elif args.action == 'passwd':
	try:
		user = user_get( args.username )
		password = get_password( args )
		user.set_password( password )
		user.save()
	except ServiceUser.DoesNotExist:
		print( "Error: %s: User does not exist."%args.username )
		sys.exit(1)
	except errors.PasswordInvalid as e:
		print( "Error: %s"%e )
		sys.exit(1)
elif args.action == 'view':
	try:
		user = user_get( args.username )
		print( 'Joined: %s'%( user.date_joined ) )
		print( 'Last login: %s'%(user.last_login) )
		
		if args.service:
			service = Service.objects.get( username=args.service )
			groups = user.group_set.filter( service=service ).values_list('service__username', flat=True)
			print( 'Groups: %s'%(', '.join( groups )))
		else:
			groups_dict = {}
			qs = user.group_set.values_list( 'service__username', 'name' )
			for service, name in qs:
				if service in groups_dict:
					groups_dict[service].append( name )
				else:
					groups_dict[service] = [name]

		
			print( 'Groups: ' )

			for service in sorted( groups_dict ):
				groups = groups_dict[service]
				if service == None:
					service = 'no-service'
				print( '* %s: %s'%(service, ', '.join( groups )))
	except Service.DoesNotExist:
		print( "Error: %s: Service does not exist."%args.service )
		sys.exit(1)
	except ServiceUser.DoesNotExist:
		print( "Error: %s: User does not exist."%args.username )
		sys.exit(1)
elif args.action in [ 'delete', 'rm', 'remove' ]:
	try:
		user_get( args.username ).delete()
	except ServiceUser.DoesNotExist:
		print( "Error: %s: User does not exist."%args.username )
		sys.exit(1)