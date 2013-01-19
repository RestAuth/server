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

from operator import attrgetter

from RestAuth.backends import group_backend
from RestAuth.common.errors import GroupNotFound


def print_by_service(groups, indent=''):
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


def get_group(parser, name, service):
    try:
        return group_backend.get(name=name, service=service)
    except GroupNotFound:
        parser.error('%s at service %s: Group does not exist.' %
                     (name, service))
