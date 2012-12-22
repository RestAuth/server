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

import os
import sys
import getpass

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
sys.path.append(os.getcwd())

try:
    from RestAuth.Groups.models import Group
    from RestAuth.Users.models import ServiceUser, Property
    from RestAuth.Services.models import Service
    from RestAuth.common import errors
    from RestAuth.Users.cli.parsers import parser
except ImportError as e:
    sys.stderr.write('Error: Cannot import RestAuth. Please make '
                     'sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)

# parse arguments
args = parser.parse_args()


def get_password(options):
    if options.pwd:
        return options.pwd

    password = getpass.getpass('password: ')
    confirm = getpass.getpass('confirm: ')
    if password != confirm:
        print("Passwords do not match, please try again.")
        return get_password(options)
    else:
        return password

if args.action == 'add':
    try:
        password = get_password(args)
        args.user.set_password(password)
        args.user.save()
    except errors.PreconditionFailed as e:
        print("Error: %s" % e)
        sys.exit(1)
elif args.action in ['ls', 'list']:
    for user in ServiceUser.objects.values_list('username', flat=True):
        print(user.encode('utf-8'))
elif args.action == 'verify':
    if not args.pwd:
        args.pwd = getpass.getpass('password: ')
    if args.user.check_password(args.pwd):
        print('Ok.')
    else:
        print('Failed.')
        sys.exit(1)
elif args.action == 'set-password':
    try:
        password = get_password(args)
        args.user.set_password(password)
        args.user.save()
    except errors.PasswordInvalid as e:
        print("Error: %s" % e)
        sys.exit(1)
elif args.action == 'view':
    try:
        try:
            joined = args.user.property_set.get(key='date joined')
            print('Joined: %s' % joined)
        except Property.DoesNotExist:
            pass

        try:
            last_login = args.user.property_set.get(key='last login')
            print('Last login: %s' % last_login)
        except Property.DoesNotExist:
            pass

        if args.service:
            service = Service.objects.get(username=args.service)
            groups = Group.objects.member(user=args.user, service=service)
            groups = groups.values_list('name', flat=True)
            print('Groups: %s' % ', '.join(groups))
        else:
            groups_dict = {}
            qs = args.user.group_set.values_list('service__username', 'name')
            for service, name in qs:
                if service in groups_dict:
                    groups_dict[service].append(name)
                else:
                    groups_dict[service] = [name]

            print('Groups: ')

            for service in sorted(groups_dict):
                groups = groups_dict[service]
                if service is None:
                    service = 'no-service'
                print('* %s: %s' % (service, ', '.join(groups)))
    except Service.DoesNotExist:
        print("Error: %s: Service does not exist." % args.service)
        sys.exit(1)
elif args.action in ['delete', 'rm', 'remove']:
    args.user.delete()
