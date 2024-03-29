#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not, see
# <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import getpass
import os
import sys

from pkg_resources import DistributionNotFound
from pkg_resources import Requirement
from pkg_resources import resource_filename

# Setup environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RestAuth.settings')
sys.path.append(os.getcwd())
try:
    req = Requirement.parse("RestAuth")
    path = resource_filename(req, 'RestAuth')
    if os.path.exists(path):  # pragma: no cover
        sys.path.insert(0, path)
except DistributionNotFound:
    pass  # we're run in a not-installed environment

try:
    import django
    django.setup()

    import six

    from Services.models import Service
    from Users.cli.parsers import parser
    from backends import backend
    from common.errors import UserExists
    from common.errors import UserNotFound
except ImportError:  # pragma: no cover
    sys.stderr.write(
        'Error: Cannot import RestAuth. Please make sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)


def main(args=None):
    # parse arguments
    args = parser.parse_args(args=args)

    if args.action == 'add':
        password = args.get_password(args)
        if args.password_generated:
            print(args.pwd)

        backend.set_password(user=args.user, password=password)
    elif args.action in ['ls', 'list']:
        for username in sorted(backend.list_users()):
            if six.PY3:  # pragma: py3
                print(username)
            else:   # pragma: py2
                print(username.encode('utf-8'))
    elif args.action == 'verify':
        if not args.pwd:  # pragma: no cover
            args.pwd = getpass.getpass('password: ')
        if backend.check_password(user=args.user, password=args.pwd):
            print('Ok.')
        else:
            print('Failed.')
            sys.exit(1)
    elif args.action == 'set-password':
        password = args.get_password(args)
        if args.password_generated:
            print(args.pwd)

        backend.set_password(user=args.user, password=args.pwd)
    elif args.action == 'view':
        props = backend.get_properties(user=args.user)

        if 'date joined' in props:
            print('Joined: %s' % props['date joined'])

        if 'last login' in props:
            print('Last login: %s' % props['last login'])

        if args.service:
            groups = backend.list_groups(service=args.service, user=args.user)
            if groups:
                print('Groups: %s' % ', '.join(sorted(groups)))
            else:
                print('No groups.')
        else:
            if backend.SUPPORTS_GROUP_VISIBILITY:
                groups = {}
                none_groups = backend.list_groups(service=None, user=args.user)

                for service in Service.objects.all():
                    subgroups = backend.list_groups(service=service, user=args.user)
                    if subgroups:
                        groups[service.username] = subgroups

                if groups or none_groups:
                    print('Groups:')
                    if none_groups:
                        print('* no service: %s' % ', '.join(sorted(none_groups)))

                    for service, groups in sorted(groups.items(), key=lambda t: t[0]):
                        print('* %s: %s' % (service, ', '.join(sorted(groups))))
                else:
                    print('No groups.')
            else:
                groups = backend.list_groups(service=None, user=args.user)
                if groups:
                    print('Groups: %s' % ', '.join(sorted(groups)))
                else:
                    print('No groups.')
    elif args.action == 'rename':
        try:
            backend.rename_user(user=args.user, name=args.name)
        except UserNotFound as e:
            parser.error("%s: %s" % (args.name, e))
        except UserExists as e:
            parser.error("%s: %s" % (args.name, e))
    elif args.action in ['delete', 'rm', 'remove']:  # pragma: no branch
        backend.remove_user(user=args.user)


if __name__ == '__main__':  # pragma: no cover
    main()
