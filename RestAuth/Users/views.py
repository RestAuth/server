# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not,
# see <http://www.gnu.org/licenses/>.

"""This module implements all HTTP queries to ``/user/*``."""

from __future__ import unicode_literals

import logging

from datetime import datetime

from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils import six

from RestAuthCommon.strprep import stringcheck

from Users.validators import validate_username
from backends import backend
from common.errors import PasswordInvalid
from common.errors import UserNotFound
from common.responses import HttpResponseCreated
from common.responses import HttpResponseNoContent
from common.responses import HttpRestAuthResponse
from common.types import parse_dict
from common.views import RestAuthResourceView
from common.views import RestAuthSubResourceView
from common.views import RestAuthView


class UsersView(RestAuthView):
    """Handle requests to ``/users/``."""

    http_method_names = ['get', 'post']
    log = logging.getLogger('users')
    post_format = {
        'mandatory': (('user', six.string_types),),
        'optional': (
            ('password', six.string_types),
            ('properties', dict),
        ),
    }
    post_required = (('user', six.string_types),)
    post_optional = (
        ('password', six.string_types),
        ('properties', dict),
        ('groups', list),
    )

    def get(self, request, largs, *args, **kwargs):
        """Get all users."""

        if not request.user.has_perm('Users.users_list'):
            return HttpResponseForbidden()

        names = [n.lower() for n in backend.list_users()]
        return HttpRestAuthResponse(request, names)

    def post(self, request, largs, dry=False):
        """Create a new user."""

        if not request.user.has_perm('Users.user_create'):
            return HttpResponseForbidden()

        name, password, properties, groups = self._parse_post(request)
        name = stringcheck(name)

        # If UsernameInvalid: 412 Precondition Failed
        validate_username(name)

        # check password:
        if password:
            if len(password) < settings.MIN_PASSWORD_LENGTH:
                # If PasswordInvalid: 412 Precondition Failed
                raise PasswordInvalid("Password too short")
        else:
            password = None

        # normalize properties, add date-joined if not present
        if properties is None:
            properties = {
                'date joined': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        else:
            properties = {stringcheck(k): v for k, v in six.iteritems(properties)}
            if 'date joined' not in properties:
                properties['date joined'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # normalize groups
        if groups:
            groups = [(stringcheck(g), request.user) for g in groups]

        # If UserExists: 409 Conflict
        backend.create_user(user=name, password=password, properties=properties, groups=groups,
                            dry=dry)
        self.log.info('%s: Created user', name, extra=largs)

        return HttpResponseCreated()


class UserHandlerView(RestAuthResourceView):
    """Handle requests to ``/users/<user>/``."""

    http_method_names = ['get', 'post', 'put', 'delete']
    log = logging.getLogger('users.user')
    post_required = (('password', six.string_types),)
    post_optional = (
        ('groups', list),
    )
    put_optional = (('password', six.string_types),)

    def get(self, request, largs, name):
        """Verify that a user exists."""

        if not request.user.has_perm('Users.user_exists'):
            return HttpResponseForbidden()

        if backend.user_exists(user=name):
            return HttpResponseNoContent()
        else:
            raise UserNotFound(name)  # 404 Not Found

    def post(self, request, largs, name):
        """Verify a users password."""

        if not request.user.has_perm('Users.user_verify_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password, groups = self._parse_post(request)
        if groups is not None:
            groups = [(group, request.user) for group in groups]

        if backend.check_password(user=name, password=password, groups=groups):
            return HttpResponseNoContent()
        else:
            raise UserNotFound(name)

    def put(self, request, largs, name):
        """Change a users password."""

        if not request.user.has_perm('Users.user_change_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password = self._parse_put(request)
        if password:
            if len(password) < settings.MIN_PASSWORD_LENGTH:
                raise PasswordInvalid("Password too short")
        else:
            password = None

        # If UserNotFound: 404 Not Found
        backend.set_password(user=name, password=password)
        return HttpResponseNoContent()

    def delete(self, request, largs, name):
        """Delete a user."""

        if not request.user.has_perm('Users.user_delete'):
            return HttpResponseForbidden()

        # If UserNotFound: 404 Not Found
        backend.remove_user(user=name)
        return HttpResponseNoContent()


class UserPropsIndex(RestAuthResourceView):
    """Handle requests to ``/users/<user>/props/``."""

    log = logging.getLogger('users.user.props')
    http_method_names = ['get', 'post', 'put']
    post_required = (('prop', six.string_types), ('value', six.string_types),)

    def get(self, request, largs, name):
        """Get all properties of a user."""

        if not request.user.has_perm('Users.props_list'):
            return HttpResponseForbidden()

        # If UserNotFound: 404 Not Found
        props = backend.list_properties(user=name)
        return HttpRestAuthResponse(request, props)

    def post(self, request, largs, name, dry=False):
        """Create a new property."""

        if not request.user.has_perm('Users.prop_create'):
            return HttpResponseForbidden()

        # If AssertionError: 400 Bad Request
        key, value = self._parse_post(request)
        key = stringcheck(key)

        # If UserNotFound: 404 Not Found
        # If PropertyExists: 409 Conflict
        backend.create_property(username=name, key=key, value=value, dry=dry)

        self.log.info('Created property "%s" as "%s"', key, value, extra=largs)
        return HttpResponseCreated()

    def put(self, request, largs, name):
        """Set multiple properties."""

        if not request.user.has_perm('Users.prop_create'):
            return HttpResponseForbidden()

        properties = {stringcheck(k): v for k, v in six.iteritems(parse_dict(request))}

        # If UserNotFound: 404 Not Found
        backend.set_properties(user=name, properties=properties)
        return HttpResponseNoContent()


class UserPropHandler(RestAuthSubResourceView):
    """Handle requests to ``/users/<user>/props/<prop>/``."""

    log = logging.getLogger('users.user.props.prop')
    http_method_names = ['get', 'put', 'delete']
    put_required = (('value', six.string_types),)

    def get(self, request, largs, name, subname):
        """Get value of a single property."""

        if not request.user.has_perm('Users.prop_get'):
            return HttpResponseForbidden()

        # If UserNotFound: 404 Not Found
        value = backend.get_property(user=name, key=subname)

        if request.version < (0, 7):
            return HttpRestAuthResponse(request, value)
        else:
            return HttpRestAuthResponse(request, {'value': value})

    def put(self, request, largs, name, subname):
        """Set value of a single property."""

        if not request.user.has_perm('Users.prop_set'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        value = self._parse_put(request)

        # If UserNotFound: 404 Not Found
        old_value = backend.set_property(user=name, key=subname, value=value)

        if old_value is None:  # new property
            self.log.info('Set to "%s"', value, extra=largs)
            return HttpResponseCreated()
        else:  # existing property
            self.log.info('Changed from "%s" to "%s"', old_value, value, extra=largs)

            if request.version < (0, 7):
                return HttpRestAuthResponse(request, old_value)
            else:
                return HttpRestAuthResponse(request, {'value': old_value})

    def delete(self, request, largs, name, subname):
        """Delete a property."""

        if not request.user.has_perm('Users.prop_delete'):
            return HttpResponseForbidden()

        # If UserNotFound: 404 Not Found
        backend.remove_property(user=name, key=subname)
        return HttpResponseNoContent()
