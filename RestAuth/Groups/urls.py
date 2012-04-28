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

from django.conf.urls.defaults import *

urlpatterns = patterns('RestAuth.Groups.views',
    (r'^$', 'index'),
    (r'^(?P<groupname>[^/]+)/$', 'group_handler' ),
    (r'^(?P<groupname>[^/]+)/users/$', 'group_users_index_handler' ),
    (r'^(?P<groupname>[^/]+)/users/(?P<username>[^/]+)/$', 'group_user_handler' ),
    (r'^(?P<groupname>[^/]+)/groups/$', 'group_groups_index_handler' ),
    (r'^(?P<meta_groupname>[^/]+)/groups/(?P<sub_groupname>[^/]+)/$', 'group_groups_handler' ),
)
