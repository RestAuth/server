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
from argparse import ArgumentParser
from operator import attrgetter

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
sys.path.append(os.getcwd())

try:
    from RestAuth.Groups.models import Group, group_create
    from RestAuth.Users.models import ServiceUser, user_get
    from RestAuth.Services.models import Service
    from RestAuth.common.cli import group_parser
except ImportError:
    sys.stderr.write('Error: Cannot import RestAuth. '
                     'Please make sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)

# parse arguments
args = group_parser.parse_args()


def print_groups_by_service(groups, indent=''):
    servs = {}
    for group in groups:
        if group.service in servs:
            servs[group.service].append(group)
        else:
            servs[group.service] = [group]

    if None in servs:
        none_names = [service.name.encode('utf-8') for service in servs[None]]
        none_names.sort()
        print('%sNone: %s' % (indent, ', '.join(none_names)))
        del servs[None]

    service_names = sorted(servs.keys(), key=attrgetter('username'))

    for name in service_names:
        names = [service.name.encode('utf-8') for service in servs[name]]
        names.sort()
        print('%s%s: %s' % (indent, name, ', '.join(names)))

if args.service:
    service = Service.objects.get(username=args.service)
else:
    service = None

# Actions that do not act on an existing group:
if args.action in ['create', 'add']:
    group_create(args.group.decode('utf-8'), service)
    sys.exit()
elif args.action in ['list', 'ls']:
    qs = Group.objects.values_list('name', flat=True).order_by('name')
    if args.service:
        groups = qs.filter(service__username=args.service)
    else:
        groups = qs.filter(service=None)
    for group in groups:
        print(group.encode('utf-8'))
    sys.exit()

try:
    group = Group.objects.get(name=args.group, service=service)
except Group.DoesNotExist:
    print('Error: %s: Group does not exist' % args.group)
    sys.exit(1)

# Actions that act on an existing group:
if args.action == 'view':
    explicit_users = group.get_members(depth=0)
    effective_users = group.get_members()
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
        print_groups_by_service(parent_groups, '    ')
    else:
        print('* No parent groups')
    if sub_groups:
        print('* Subgroups:')
        print_groups_by_service(sub_groups, '    ')
    else:
        print('* No subgroups')
elif args.action == 'add-user':
    user = ServiceUser.objects.get(username=args.user.lower())

    group.users.add(user)
elif args.action == 'add-group':
    if args.sub_service:
        sub_service = Service.objects.get(username=args.sub_service)
    else:
        sub_service = None
    sub_group = Group.objects.get(name=args.subgroup, service=sub_service)

    sub_group.parent_groups.add(group)
elif args.action in ['delete', 'del', 'rm']:
    group.delete()
elif args.action in ['remove-user', 'rm-user', 'del-user']:
    user = ServiceUser.objects.get(username=args.user.lower())
    if user in group.users.all():
        group.users.remove(user)
elif args.action in ['remove-group', 'rm-group', 'del-group']:
    try:
        if args.sub_service:
            sub_service = Service.objects.get(username=args.sub_service)
            sub_group = Group.objects.get(
                name=args.subgroup, service=sub_service)
        else:
            sub_group = Group.objects.get(name=args.subgroup, service=None)
    except Group.DoesNotExist:
        print('Error: %s: Does not exist' % args.subgroup)
        sys.exit(1)

    if sub_group in group.groups.all():
        sub_group.parent_groups.remove(group)
