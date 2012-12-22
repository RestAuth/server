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

import getpass
import os
import sys

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
sys.path.append(os.getcwd())

try:
    from RestAuth.Services.models import Service
    from RestAuth.Services.cli import parser
except ImportError as e:
    print(e)
    sys.stderr.write('Error: Cannot import RestAuth. Please make sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)

args = parser.parse_args()


def get_password(args):
    if args.pwd:
        return args.pwd

    password = getpass.getpass('password: ')
    confirm = getpass.getpass('confirm: ')
    if password != confirm:
        print("Passwords do not match, please try again.")
        return get_password(args)
    else:
        return password


if args.action == 'add':
    if args.password_generated:
        print(args.pwd)

    args.service.set_password(get_password(args))
    args.service.save()
elif args.action == 'rm':
    args.service.delete()
elif args.action == 'ls':
    for service in Service.objects.all().order_by('username'):
        hosts = [host.address for host in service.hosts.all()]
        print('%s: %s' % (service.username, ', '.join(hosts)))
elif args.action == 'view':
    print(args.service.username)
    print('Last used: %s' % (args.service.last_login))
    hosts = [str(host.address) for host in args.service.hosts.all()]
    print('Hosts: %s' % (', '.join(hosts)))
    perms = [p.codename for p in args.service.user_permissions.all()]
    print('Permissions: %s' % (', '.join(perms)))
elif args.action == 'set-hosts':
    args.service.set_hosts(*args.hosts)
elif args.action == 'add-hosts':
    args.service.add_hosts(*args.hosts)
elif args.action == 'rm-hosts':
    args.service.del_hosts(*args.hosts)
elif args.action == 'set-password':
    if args.password_generated:
        print(args.pwd)

    args.service.set_password(get_password(args))
    args.service.save()
elif args.action == 'set-permissions':
    args.service.user_permissions.clear()
    args.service.user_permissions.add(*args.permissions)
elif args.action == 'add-permissions':
    args.service.user_permissions.add(*args.permissions)
elif args.action == 'rm-permissions':
    args.service.user_permissions.remove(*args.permissions)
