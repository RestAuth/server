# -*- coding: utf-8 -*-
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

import fnmatch

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from RestAuth.Users.models import user_permissions, prop_permissions
from RestAuth.Groups.models import group_permissions


class PermissionParser(Action):
    def __call__(self, parser, namespace, values, option_string):
        user_ct = ContentType.objects.get(app_label='Users',
                                          model='serviceuser')
        prop_ct = ContentType.objects.get(app_label='Users', model='property')
        group_ct = ContentType.objects.get(app_label='Groups', model='group')

        user_permissions_dict = dict(user_permissions)
        prop_permissions_dict = dict(prop_permissions)
        group_permissions_dict = dict(group_permissions)

        permissions = []
        for value in values:
            for codename in fnmatch.filter(user_permissions_dict.keys(), value):
                perm, c = Permission.objects.get_or_create(
                    content_type=user_ct, codename=codename,
                    defaults={'name': user_permissions_dict[codename]}
                )
                permissions.append(perm)

            for codename in fnmatch.filter(prop_permissions_dict.keys(), value):
                perm, c = Permission.objects.get_or_create(
                    content_type=prop_ct, codename=codename,
                    defaults={'name': prop_permissions_dict[codename]}
                )
                permissions.append(perm)

            for codename in fnmatch.filter(group_permissions_dict.keys(), value):
                perm, c = Permission.objects.get_or_create(
                    content_type=group_ct, codename=codename,
                    defaults={'name': group_permissions_dict[codename]}
                )
                permissions.append(perm)

        setattr(namespace, self.dest, permissions)