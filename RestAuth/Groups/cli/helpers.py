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

from itertools import groupby

from django.utils import six

from RestAuth.backends import group_backend
from RestAuth.common.errors import GroupNotFound


def print_by_service(groups, indent=''):
    by_service = groupby(groups, key=lambda g: g.service)

    for service, groups in sorted(by_service, key=lambda t: t[0] if t[0] else ''):
        names = sorted([group.name for group in groups])
        if not six.PY3:
            names = [name.encode('utf-8') for name in names]

        if not service:
            service = '<no service>'
        print("%s%s: %s" % (indent, service, ', '.join(names)))


def get_group(parser, name, service):
    try:
        return group_backend.get(name=name, service=service)
    except GroupNotFound:
        parser.error('%s at service %s: Group does not exist.' %
                     (name, service))
