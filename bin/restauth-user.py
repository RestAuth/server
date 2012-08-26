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
from argparse import ArgumentParser

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
sys.path.append( os.getcwd() )

try:
    from RestAuth.Users.models import (ServiceUser, user_get, validate_username,
                                       Property)
    from RestAuth.Services.models import Service
    from RestAuth.common import errors
    from RestAuth.common.cli import user_parser
    from django.db.utils import IntegrityError
except ImportError, e:
    sys.stderr.write( 'Error: Cannot import RestAuth. Please make sure RestAuth is in your PYTHONPATH.\n' )
    sys.exit(1)

# parse arguments
args = user_parser.parse_args()

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
    username = args.user.decode( 'utf-8')

    try:
        validate_username( username )
        user = ServiceUser( username=username )
        password = get_password( args )
        user.set_password( password )
        user.save()
    except IntegrityError as e:
        print( "Error: %s: User already exists."%username )
        sys.exit(1)
    except errors.PreconditionFailed as e:
        print( "Error: %s"%e )
        sys.exit(1)
elif args.action in ['ls', 'list']:
    for user in ServiceUser.objects.values_list( 'username', flat=True ):
        print( user.encode('utf-8' ) )
elif args.action == 'verify':
    try:
        user = user_get( args.user )
        if not args.pwd:
            args.pwd = getpass.getpass( 'password: ' )
        if user.check_password( args.pwd ):
            print( 'Ok.' )
        else:
            print( 'Failed.' )
            sys.exit(1)
    except ServiceUser.DoesNotExist:
        print( "Error: %s: User does not exist."%args.user )
        sys.exit(1)
elif args.action == 'set-password':
    try:
        user = user_get( args.user )
        password = get_password( args )
        user.set_password( password )
        user.save()
    except ServiceUser.DoesNotExist:
        print( "Error: %s: User does not exist."%args.user )
        sys.exit(1)
    except errors.PasswordInvalid as e:
        print( "Error: %s"%e )
        sys.exit(1)
elif args.action == 'view':
    try:
        user = user_get(args.user)

        try:
            print('Joined: %s' % user.property_set.get(key='date joined'))
        except Property.DoesNotExist:
            pass

        try:
            print('Last login: %s' % user.property_set.get(key='last login'))
        except Property.DoesNotExist:
            pass

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
        print( "Error: %s: User does not exist."%args.user )
        sys.exit(1)
elif args.action in [ 'delete', 'rm', 'remove' ]:
    try:
        user_get( args.user ).delete()
    except ServiceUser.DoesNotExist:
        print( "Error: %s: User does not exist."%args.user )
        sys.exit(1)
