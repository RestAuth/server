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
desc = """%prog manages users in RestAuth. Users are clients that want to
authenticate with services that use RestAuth. Valid actions are help, add,
list, verify, set-password, groups and delete."""
prog = os.path.basename(sys.argv[0])
epilog = """Use %s help <action>  to get help for each action and their
parameters""" % (prog)
parser = OptionParser( usage=usage, description=desc, epilog=epilog)
parser.add_option( '--settings', default='RestAuth.settings',
	help="The path to the Django settings module (Usually the default is fine)." )

pwd_group = OptionGroup( parser, "Options for the actions add, verify and set-password." )
pwd_group.add_option( '--password', metavar='PWD', dest='pwd',
	help="""Use PWD for the users password. If not given, you will be
prompted.""" )
parser.add_option_group( pwd_group )

view_group = OptionGroup( parser, "Options for the 'view' action" )
view_group.add_option( '--service', 
	help="View the information as SERVICE would see it. (optional)." )
parser.add_option_group( view_group )

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
		from RestAuth.Users.models import ServiceUser, user_get, user_create, validate_username, UsernameInvalid
		from RestAuth.Services.models import service_get, ServiceNotFound
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

if args[0] in ['create', 'add']:
	if len( args ) < 2:
		print( "Please name a user to add!" )
		sys.exit(1)
	elif len( args ) > 2:
		print( "Please name exactly one user to add!" )

	try:
		validate_username( args[1] )
		user = ServiceUser( username=args[1] )
		user.save()
		password = get_password( options )
		user.set_password( password )
		user.save()
	except IntegrityError as e:
		print( e )
		print( "Error: %s: User already exists."%args[1] )
		sys.exit(1)
	except errors.PreconditionFailed as e:
		print( e )
		sys.exit(1)
elif args[0] in ['ls', 'list']:
	for user in ServiceUser.objects.all():
		print( user.username )
elif args[0] == 'verify':
	if len( args ) != 2:
		print( "Please name exactly one user to verify!" )
		sys.exit(1)

	try:
		user = user_get( args[1] )
		if not options.pwd:
			options.pwd = getpass.getpass( 'password: ' )
		if user.check_password( options.pwd ):
			print( 'Ok.' )
		else:
			print( 'Failed.' )
	except ServiceUser.DoesNotExist:
		print( "Error: %s: User does not exist."%args[1] )
		sys.exit(1)
elif args[0] == 'set-password':
	if len( args ) != 2:
		print( "Please name exactly one user to update!" )
		sys.exit(1)

	try:
		user = user_get( args[1] )
		password = get_password( options )
		user.set_password( password )
		user.save()
	except ServiceUser.DoesNotExist:
		print( "Error: %s: User does not exist."%args[1] )
		sys.exit(1)
	except errors.PasswordInvalid as e:
		print( "Error: %s"%e.body )
		sys.exit(1)
elif args[0] == 'view':
	if len( args ) != 2:
		print( "Please name a user to view!" )
		sys.exit(1)

	try:
		user = user_get( args[1] )
		if options.service:
			service = service_get( options.service )
			groups = user.get_groups( service )
		else:
			groups = user.get_groups()
	
		group_names = [ group.name for group in groups ]
		group_names.sort()

		print( 'Joined: %s'%( user.date_joined ) )
		print( 'Last login: %s'%(user.last_login) )
		print( 'Groups: %s'%(', '.join( group_names ) ) )
	except ServiceNotFound:
		print( "Error: %s: Service does not exist."%options.service )
		sys.exit(1)
	except ServiceUser.DoesNotExist:
		print( "Error: %s: User does not exist."%args[1] )
		sys.exit(1)
elif args[0] in [ 'delete', 'rm', 'remove' ]:
	if len( args ) != 2:
		print( "Please name a user to delete!" )
		sys.exit(1)

	try:
		user = user_get( args[1] )
		user.delete()
	except ServiceUser.DoesNotExist:
		print( "Error: %s: User does not exist."%args[1] )
		sys.exit(1)
elif args[0] == 'help':
	if len(args) > 1:
		help_parser = OptionParser(usage='%prog [options] ', add_help_option=False )
		help_parser.add_option( '--settings', default='RestAuth.settings',
			help="The path to the Django settings module (Usually the default is fine)." )

		if args[1] == 'add':
			help_parser.usage += 'add <user>'
			desc = """Create a new user in the database."""
			opt = parser.get_option( '--password' )
			help_parser.add_option( opt )
		elif args[1] == 'list':
			help_parser.usage += 'list'
			desc = """List all users in the RestAuth database."""
		elif args[1] == 'verify-password':
			help_parser.usage += 'verify-password <user>'
			desc = """Verify that a password is the correct password
for the given user."""
			opt = parser.get_option( '--password' )
			help_parser.add_option( opt )
		elif args[1] == 'set-password':
			help_parser.usage += 'set-password <user>'
			desc = """Update the password of the given user."""
			opt = parser.get_option( '--password' )
			help_parser.add_option( opt )
		elif args[1] == 'view':
			help_parser.usage += 'view <user>'
			desc = """View all details of the given user."""
			opt = parser.get_option( '--service' )
			help_parser.add_option( opt )
		elif args[1] == 'delete':
			help_parser.usage += 'delete <user>'
			desc = """Delete a user from the database."""
		else:
			print( "Unknown action." )
			sys.exit(1)
		help_parser.description = desc
		help_parser.print_help()
	else:
		parser.print_help()
