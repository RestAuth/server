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

from django.conf import settings
from django.db import models
from django.db.models import Q


class GroupQuerySet(models.query.QuerySet):
    def member(self, user, service=None, depth=None):
        if depth is None:  # pragma: no branch
            depth = settings.GROUP_RECURSION_DEPTH

        expr = Q(users=user, service=service)

        kwarg = 'users'
        for i in range(depth):
            kwarg = 'parent_groups__%s' % kwarg
            expr |= models.Q(**{kwarg: user, 'service': service})

        return self.filter(expr).distinct()
