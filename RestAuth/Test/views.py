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

from django.conf import settings
from django.db import transaction

from RestAuth.Users.views import UserPropsIndex
from RestAuth.Users.models import validate_username
from RestAuth.Groups.views import GroupsView
from RestAuth.Services.decorator import login_required
from RestAuth.common.types import get_dict
from RestAuth.common.utils import import_path
from RestAuth.common.responses import HttpResponseCreated

props_view = UserPropsIndex.as_view()
groups_view = GroupsView.as_view()

user_backend = import_path(getattr(
        settings, 'USER_BACKEND',
        'RestAuth.backends.django_orm.DjangoUserBackend'
))[0]()
property_backend = import_path(getattr(
        settings, 'PROPERTY_BACKEND',
        'RestAuth.backends.django_orm.DjangoPropertyBackend'
))[0]()
group_backend = import_path(getattr(
        settings, 'PROPERTY_BACKEND',
        'RestAuth.backends.django_orm.DjangoGroupBackend'
))[0]()


@login_required(realm="/test/users/")
def users(request):
    # If BadRequest: 400 Bad Request
    name, password, props = get_dict(
        request, [u'user'], [u'password', u'properties'])

    # If UsernameInvalid: 412 Precondition Failed
    validate_username(name)

    # If ResourceExists: 409 Conflict
    # If PasswordInvalid: 412 Precondition Failed
    user = user_backend.create(name, password, props, dry=True)
    return HttpResponseCreated(request, user)


@login_required(realm="/test/users/<user>/props/")
def users_user_props(request, name):
    # If BadRequest: 400 Bad Request
    key, value = get_dict(request, [u'prop', u'value'])

    # If User.DoesNotExist: 404 Not Found
    # If PropertyExists: 409 Conflict
    prop = property_backend.create(name, key, value, dry=True)
    return HttpResponseCreated(request, prop)


@login_required(realm="/test/groups/")
@transaction.commit_manually
def groups(request):
    try:
        return groups_view(request)
    finally:
        transaction.rollback()
