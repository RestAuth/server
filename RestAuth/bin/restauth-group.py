#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

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

    from Groups.cli.helpers import print_by_service
    from Groups.cli.parsers import parser
    from backends import backend
    from common.errors import GroupExists
    from common.errors import GroupNotFound
    from common.errors import UserNotFound
except ImportError as e:  # pragma: no cover
    sys.stderr.write(
        'Error: Cannot import RestAuth. Please make sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)


def _main(args):
    # Actions that do not act on an existing group:
    if args.action == 'add':
        try:
            backend.create_group(group=args.group, service=args.service)
        except GroupExists:
            parser.error('Group already exists.')
    elif args.action in ['list', 'ls']:
        groups = backend.list_groups(service=args.service)

        for name in sorted(groups):
            print(name)
    elif args.action == 'view':
        explicit_users = sorted(backend.members(group=args.group, service=args.service, depth=0))
        effective_users = sorted(backend.members(group=args.group, service=args.service))

        if explicit_users:
            print('* Explicit members: %s' % ', '.join(explicit_users))
        else:
            print('* No explicit members')
        if backend.SUPPORTS_SUBGROUPS:
            if effective_users:
                print('* Effective members: %s' % ', '.join(effective_users))
            else:
                print('* No effective members')

        if backend.SUPPORTS_SUBGROUPS is True:
            parents = backend.parents(group=args.group, service=args.service)
            sub_groups = backend.subgroups(group=args.group, service=args.service, filter=False)

            if parents:
                if backend.SUPPORTS_GROUP_VISIBILITY:
                    print('* Parent groups:')
                    parents = sorted(parents, key=lambda g: g[1].username if g[1] else '')
                    print_by_service(parents, '    ')
                else:
                    print('* Parent groups: %s' % ', '.join([g[0] for g in parents]))
            else:
                print('* No parent groups')

            if sub_groups:
                if backend.SUPPORTS_GROUP_VISIBILITY:
                    print('* Subgroups:')
                    sub_groups = sorted(sub_groups, key=lambda g: g[1].username if g[1] else '')
                    print_by_service(sub_groups, '    ')
                else:
                    print('* Subgroups: %s' % ', '.join([g[0] for g in sub_groups]))
            else:
                print('* No subgroups')
    elif args.action == 'set-service':
        if backend.SUPPORTS_GROUP_VISIBILITY is False:
            parser.error('Backend does not support group visiblity.')
        backend.set_service(group=args.group, service=args.service,
                                  new_service=args.new_service)
    elif args.action == 'add-user':
        backend.add_member(group=args.group, service=args.service, user=args.user)
    elif args.action == 'add-group':
        if backend.SUPPORTS_SUBGROUPS is False:
            parser.error('Backend does not support subgroups.')
        backend.add_subgroup(group=args.group, service=args.service, subgroup=args.subgroup,
                             subservice=args.sub_service)
    elif args.action in ['delete', 'del', 'rm']:
        backend.remove_group(group=args.group, service=args.service)
    elif args.action in ['remove-user', 'rm-user', 'del-user']:
        try:
            backend.remove_member(group=args.group, service=args.service, user=args.user)
        except UserNotFound:
            parser.error('User "%s" not member of group "%s".' % (args.user, args.group))
    elif args.action == 'rename':
        backend.rename_group(args.group, args.name, service=args.service)
    elif args.action in ['remove-group', 'rm-group', 'del-group']:  # pragma: no branch
        if backend.SUPPORTS_SUBGROUPS is False:
            parser.error('Backend does not support subgroups.')
        try:
            backend.remove_subgroup(group=args.group, service=args.service, subgroup=args.subgroup,
                                    subservice=args.sub_service)
        except GroupNotFound:
            parser.error('Group "%s" is not a subgroup of "%s".' % (args.subgroup, args.group))


def main(args=None):
    args = parser.parse_args(args)
    try:
        _main(args)
    except GroupNotFound:
        parser.error('%s at service %s: Group does not exist.' % (args.group, args.service))
    except GroupExists as e:
        parser.error("%s: Group already exists." % e.args[0])

if __name__ == '__main__':  # pragma: no cover
    main()
