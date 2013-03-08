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
    from RestAuth.Services.models import Service
    from RestAuth.Users.cli.parsers import parser
    from RestAuth.backends import user_backend
    from RestAuth.backends import property_backend
    from RestAuth.backends import group_backend
    from RestAuth.common import errors
except ImportError as e:
    print e
    sys.stderr.write('Error: Cannot import RestAuth. Please make '
                     'sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)

# parse arguments
args = parser.parse_args()

if args.action == 'add':
    try:
        password = args.get_password(args)
        if args.password_generated:
            print(args.pwd)

        user_backend.set_password(args.user.username, password)
    except errors.PreconditionFailed as e:
        print("Error: %s" % e)
        sys.exit(1)
elif args.action in ['ls', 'list']:
    for username in sorted(user_backend.list()):
        print(username.encode('utf-8'))
elif args.action == 'verify':
    if not args.pwd:
        args.pwd = getpass.getpass('password: ')
    if user_backend.check_password(args.user.username, args.pwd):
        print('Ok.')
    else:
        print('Failed.')
        sys.exit(1)
elif args.action == 'set-password':
    try:
        password = args.get_password(args)
        if args.password_generated:
            print(args.pwd)

        user_backend.set_password(args.user.username, args.pwd)
    except errors.PasswordInvalid as e:
        print("Error: %s" % e)
        sys.exit(1)
elif args.action == 'view':
    props = property_backend.list(args.user)

    if 'date joined' in props:
        print('Joined: %s' % props['date joined'])

    if 'last login' in props:
        print('Last login: %s' % props['last login'])

    if args.service:
        groups = group_backend.list(service=args.service, user=args.user)
        print('Groups: %s' % ', '.join(sorted(groups)))
    else:
        print('Groups: ')
        no_service_groups = group_backend.list(service=None, user=args.user)
        if no_service_groups:
            print('* no service: %s' % ', '.join(sorted(no_service_groups)))

        for service in Service.objects.all():
            groups = group_backend.list(service=service, user=args.user)
            if groups:
                print('* %s: %s' % (service.username, ', '.join(sorted(groups))))
elif args.action in ['delete', 'rm', 'remove']:
    user_backend.remove(args.user.username)
