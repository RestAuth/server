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

from Groups.views import GroupsView
from Services.decorator import login_required
from Users.views import UserPropsIndex
from Users.views import UsersView

users_view = UsersView.as_view()
props_view = UserPropsIndex.as_view()
groups_view = GroupsView.as_view()


@login_required(realm="/test/users/")
def users(request):
    return users_view(request, dry=True)


@login_required(realm="/test/users/<user>/props/")
def users_user_props(request, name):
    return props_view(request, name, dry=True)


@login_required(realm="/test/groups/")
def groups(request):
    return groups_view(request, dry=True)
