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

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
sys.path.append(os.getcwd())

from django.db.utils import IntegrityError

try:
    from RestAuth.Groups.models import Group
    from RestAuth.Groups.cli import parser, get_group, print_by_service
except ImportError as e:
    sys.stderr.write('Error: Cannot import RestAuth. '
                     'Please make sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)

# parse arguments
args = parser.parse_args()

# Actions that do not act on an existing group:
if args.action == 'add':
    try:
        Group.objects.create(name=args.group, service=args.service)
    except IntegrityError:
        parser.error('Group already exists.')
elif args.action in ['list', 'ls']:
    qs = Group.objects.values_list('name', flat=True).order_by('name')
    if args.service:
        groups = qs.filter(service=args.service)
    else:
        groups = qs.filter(service=None)
    for group in groups:
        print(group.encode('utf-8'))
elif args.action == 'view':
    group = get_group(parser, args.group, args.service)
    explicit_users = group.get_members(depth=0).values_list(
        'username', flat=True)
    effective_users = group.get_members().values_list('username', flat=True)
    parent_groups = list(group.parent_groups.all())
    sub_groups = list(group.groups.all())
    if explicit_users:
        print('* Explicit members: %s' % ', '.join(sorted(explicit_users)))
    else:
        print('* No explicit members')
    if effective_users:
        print('* Effective members: %s' % ', '.join(sorted(effective_users)))
    else:
        print('* No effective members')
    if parent_groups:
        print('* Parent groups:')
        print_by_service(parent_groups, '    ')
    else:
        print('* No parent groups')
    if sub_groups:
        print('* Subgroups:')
        print_by_service(sub_groups, '    ')
    else:
        print('* No subgroups')
elif args.action == 'add-user':
    group = get_group(parser, args.group, args.service)
    group.users.add(args.user)
elif args.action == 'add-group':
    group = get_group(parser, args.group, args.service)
    sub_group = get_group(parser, args.subgroup, args.sub_service)

    sub_group.parent_groups.add(group)
elif args.action in ['delete', 'del', 'rm']:
    group = get_group(parser, args.group, args.service)
    group.delete()
elif args.action in ['remove-user', 'rm-user', 'del-user']:
    group = get_group(parser, args.group, args.service)
    if args.user in group.users.all():
        group.users.remove(args.user)
elif args.action in ['remove-group', 'rm-group', 'del-group']:
    group = get_group(parser, args.group, args.service)
    sub_group = get_group(parser, args.subgroup, args.sub_service)

    if sub_group in group.groups.all():
        sub_group.parent_groups.remove(group)
