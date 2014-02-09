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

from __future__ import unicode_literals

from django.conf.urls import patterns
from django.conf.urls import url

from Services.decorator import login_required
from Users.views import UserHandlerView
from Users.views import UserPropHandler
from Users.views import UserPropsIndex
from Users.views import UsersView

urlpatterns = patterns(
    'Users.views',

    url(r'^$', login_required(realm='/users/')(UsersView.as_view()),
        name="users",
    ),
    url(r'^(?P<name>[^/]+)/$',
        login_required(realm='/users/<user>/')(UserHandlerView.as_view()),
        name="users.user",
    ),
    url(r'^(?P<name>[^/]+)/props/$',
        login_required(realm='/users/<user>/props/')(
            UserPropsIndex.as_view()),
        name='users.user.props'
    ),
    url(r'^(?P<name>[^/]+)/props/(?P<subname>.+)/$',
        login_required(realm='/users/<user>/props/<prop>/')(
            UserPropHandler.as_view()),
        name='users.user.props.prop'
    ),
)
