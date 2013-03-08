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

try:
    from RestAuth.Groups.cli.parsers import parser
    from RestAuth.Groups.cli_parsers import get_group
    from RestAuth.Groups.cli_parsers import print_by_service
    from RestAuth.backends.utils import group_backend
    from RestAuth.common.errors import GroupExists
    from RestAuth.common.errors import GroupNotFound
    from RestAuth.common.errors import UserNotFound
except ImportError as e:
    sys.stderr.write('Error: Cannot import RestAuth. '
                     'Please make sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)

group_backend = group_backend()

# parse arguments
args = parser.parse_args()

# Actions that do not act on an existing group:
if args.action == 'add':
    try:
        group_backend.create(name=args.group, service=args.service)
    except GroupExists:
        parser.error('Group already exists.')
elif args.action in ['list', 'ls']:
    if args.service:
        groups = group_backend.list(service=args.service)
    else:
        groups = group_backend.list(service=None)
    for name in sorted(groups):
        print(name.encode('utf-8'))
elif args.action == 'view':
    group = get_group(parser, args.group, args.service)

    explicit_users = sorted(group_backend.members(group, depth=0))
    effective_users = sorted(group_backend.members(group))
    parent_groups = sorted(group_backend.parents(group))
    sub_groups = sorted(group_backend.subgroups(group, filter=False))

    if explicit_users:
        print('* Explicit members: %s' % ', '.join(explicit_users))
    else:
        print('* No explicit members')
    if effective_users:
        print('* Effective members: %s' % ', '.join(effective_users))
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
    group_backend.add_user(group, args.user)
elif args.action == 'add-group':
    group = get_group(parser, args.group, args.service)
    subgroup = get_group(parser, args.subgroup, args.sub_service)

    group_backend.add_subgroup(group, subgroup)
elif args.action in ['delete', 'del', 'rm']:
    group_backend.remove(args.service, args.group)
elif args.action in ['remove-user', 'rm-user', 'del-user']:
    group = get_group(parser, args.group, args.service)
    try:
        group_backend.rm_user(group, args.user)
    except UserNotFound:
        parser.error('User "%s" not member of group %s.' %
                     (args.user.username, group.name))
elif args.action in ['remove-group', 'rm-group', 'del-group']:
    group = get_group(parser, args.group, args.service)
    subgroup = get_group(parser, args.subgroup, args.sub_service)

    try:
        group_backend.rm_subgroup(group, subgroup)
    except GroupNotFound:
        parser.error('Group "%s" is not a subgroup of "%s".' %
                     (subgroup.name, group.name))
