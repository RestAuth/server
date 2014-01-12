#!/usr/bin/env python
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import sys

# Setup environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RestAuth.settings')
sys.path.append(os.getcwd())

try:
    from django.core.exceptions import ValidationError
    from django.db import transaction
    from django.db.utils import IntegrityError

    from Services.models import Service
    from Services.cli.parsers import parser
except ImportError as e:  # pragma: no cover
    sys.stderr.write(
        'Error: Cannot import RestAuth. Please make sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)


def main(args=None):
    args = parser.parse_args(args=args)

    if args.action == 'add':
        password = args.get_password(args)
        if args.password_generated:
            print(args.pwd)

        args.service.set_password(password)
        args.service.save()
    elif args.action == 'rename':
        args.service.username = args.name
        with transaction.atomic():
            try:
                args.service.save()
            except IntegrityError:
                parser.error("%s: Service already exists." % args.name)
    elif args.action == 'rm':
        args.service.delete()
    elif args.action == 'ls':
        for service in Service.objects.all().order_by('username'):
            print('%s: %s' % (service.name, ', '.join(service.addresses)))
    elif args.action == 'view':
        print('Last used: %s' % (args.service.last_login))
        print('Hosts: %s' % (', '.join(args.service.addresses)))
        print('Permissions: %s' % (', '.join(args.service.permissions)))
    elif args.action == 'set-hosts':
        try:
            args.service.set_hosts(*args.hosts)
        except ValidationError as e:
            parser.error(e.messages[0])
    elif args.action == 'add-hosts':
        try:
            args.service.add_hosts(*args.hosts)
        except ValidationError as e:
            parser.error(e.messages[0])
    elif args.action == 'rm-hosts':
        args.service.del_hosts(*args.hosts)
    elif args.action == 'set-password':
        password = args.get_password(args)
        if args.password_generated:
            print(args.pwd)

        args.service.set_password(password)
        args.service.save()
    elif args.action == 'set-permissions':
        args.service.user_permissions.clear()
        args.service.user_permissions.add(*args.permissions)
    elif args.action == 'add-permissions':
        args.service.user_permissions.add(*args.permissions)
    elif args.action == 'rm-permissions':  # pragma: no-branch
        args.service.user_permissions.remove(*args.permissions)

if __name__ == '__main__':  # pragma: no cover
    main()
