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

from itertools import groupby


def print_by_service(groups, indent=''):
    def keyfunc(g):
        return g[1].username if g[1] else ''

    sorted_groups = sorted(groups, key=keyfunc)  # sort by service
    by_service = groupby(sorted_groups, key=keyfunc)  # group by service

    for service, groups in by_service:
        names = sorted([g[0] for g in groups])

        if not service:
            service = '<no service>'
        print("%s%s: %s" % (indent, service, ', '.join(names)))
