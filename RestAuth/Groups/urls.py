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

from django.conf.urls import patterns
from django.conf.urls import url

from Groups.views import GroupGroupHandler
from Groups.views import GroupGroupsIndex
from Groups.views import GroupHandlerView
from Groups.views import GroupUserHandler
from Groups.views import GroupUsersIndex
from Groups.views import GroupsView
from Services.decorator import login_required

urlpatterns = patterns(
    'Groups.views',

    url(r'^$', login_required(realm='/groups/')(GroupsView.as_view()), name='groups'),
    url(r'^(?P<name>[^/]+)/$',
        login_required(realm='/groups/<group>/')(GroupHandlerView.as_view()), name='groups.group'),
    url(r'^(?P<name>[^/]+)/users/$',
        login_required(realm='/groups/<group>/users/')(GroupUsersIndex.as_view()),
        name='groups.group.users'),
    url(r'^(?P<name>[^/]+)/users/(?P<subname>[^/]+)/$',
        login_required(realm='/groups/<group>/users/<username>')(GroupUserHandler.as_view()),
        name='groups.group.users.user'),
    url(r'^(?P<name>[^/]+)/groups/$',
        login_required(realm='/groups/<group>/groups/')(GroupGroupsIndex.as_view()),
        name='groups.group.groups'),
    url(r'^(?P<name>[^/]+)/groups/(?P<subname>[^/]+)/$',
        login_required(realm='/groups/<group>/groups/<subgroupname>')(
            GroupGroupHandler.as_view()),
        name='groups.group.groups.group'),
)
