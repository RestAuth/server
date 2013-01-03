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

"""
This module implements all HTTP queries to ``/user/*``.
"""

import logging

from django.conf import settings
from django.http import HttpResponseForbidden

from RestAuthCommon import resource_validator
from RestAuthCommon.error import PreconditionFailed

from RestAuth.Users.validators import validate_username
from RestAuth.backends.utils import user_backend, property_backend
from RestAuth.common.types import get_dict, get_freeform_dict
from RestAuth.common.errors import PasswordInvalid, UserNotFound
from RestAuth.common.responses import HttpResponseCreated
from RestAuth.common.responses import HttpResponseNoContent
from RestAuth.common.responses import HttpRestAuthResponse
from RestAuth.common.views import (RestAuthView, RestAuthResourceView,
                                   RestAuthSubResourceView)

user_backend = user_backend()
property_backend = property_backend()


class UsersView(RestAuthView):
    """
    Handle requests to ``/users/``.
    """
    http_method_names = ['get', 'post']
    log = logging.getLogger('users')

    def get(self, request, largs, *args, **kwargs):
        """
        Get all users.
        """
        if not request.user.has_perm('Users.users_list'):
            return HttpResponseForbidden()

        names = user_backend.list()
        return HttpRestAuthResponse(request, names)

    def post(self, request, largs, dry=False):
        """
        Create a new user.
        """
        if not request.user.has_perm('Users.user_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        name, password, props = get_dict(
            request, [u'user'], [u'password', u'properties'])

        if not resource_validator(name):
            raise PreconditionFailed("Username contains invalid characters")
        if password is not None and password != '':
            if len(password) < settings.MIN_PASSWORD_LENGTH:
                raise PasswordInvalid("Password too short")

        # If UsernameInvalid: 412 Precondition Failed
        validate_username(name)

        # If ResourceExists: 409 Conflict
        # If PasswordInvalid: 412 Precondition Failed
        user = user_backend.create(username=name, password=password,
                                   properties=props,
                                   property_backend=property_backend,
                                   dry=dry)

        self.log.info('%s: Created user', user.username, extra=largs)
        return HttpResponseCreated(request, 'users.user', name=user.username)


class UserHandlerView(RestAuthResourceView):
    """
    Handle requests to ``/users/<user>/``.
    """
    http_method_names = ['get', 'post', 'put', 'delete']
    log = logging.getLogger('users.user')

    def get(self, request, largs, name):
        """
        Verify that a user exists.
        """
        if not request.user.has_perm('Users.user_exists'):
            return HttpResponseForbidden()

        if user_backend.exists(username=name):
            return HttpResponseNoContent()
        else:
            raise UserNotFound(name)  # 404 Not Found

    def post(self, request, largs, name):
        """
        Verify a users password.
        """
        if not request.user.has_perm('Users.user_verify_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password = get_dict(request, [u'password'])

        if user_backend.check_password(username=name, password=password):
            return HttpResponseNoContent()
        else:
            raise UserNotFound(name)

    def put(self, request, largs, name):
        """
        Change a users password.
        """
        if not request.user.has_perm('Users.user_change_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password, = get_dict(request, optional=[u'password'])
        if password is not None and password != '':
            if len(password) < settings.MIN_PASSWORD_LENGTH:
                raise PasswordInvalid("Password too short")

        user_backend.set_password(username=name, password=password)
        return HttpResponseNoContent()

    def delete(self, request, largs, name):
        """
        Delete a user.
        """
        if not request.user.has_perm('Users.user_delete'):
            return HttpResponseForbidden()

        user_backend.remove(username=name)
        return HttpResponseNoContent()


class UserPropsIndex(RestAuthResourceView):
    """
    Handle requests to ``/users/<user>/props/``.
    """
    log = logging.getLogger('users.user.props')
    http_method_names = ['get', 'post', 'put']

    def get(self, request, largs, name):
        """
        Get all properties of a user.
        """
        if not request.user.has_perm('Users.props_list'):
            return HttpResponseForbidden()

        # If UserNotFound: 404 Not Found
        user = user_backend.get(username=name)

        props = property_backend.list(user=user)
        return HttpRestAuthResponse(request, props)

    def post(self, request, largs, name, dry=False):
        """
        Create a new property.
        """
        if not request.user.has_perm('Users.prop_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        key, value = get_dict(request, [u'prop', u'value'])
        if not resource_validator(key):
            raise PreconditionFailed("Property contains invalid characters")

        # If UserNotFound: 404 Not Found
        user = user_backend.get(username=name)

        # If PropertyExists: 409 Conflict
        key, value = property_backend.create(user=user, key=key,
                                             value=value, dry=dry)

        self.log.info(
            'Created property "%s" as "%s"', key, value, extra=largs)
        return HttpResponseCreated(request, 'users.user.props.prop',
                                   name=name, subname=key)

    def put(self, request, largs, name):
        """
        Set multiple properties.
        """
        if not request.user.has_perm('Users.prop_create'):
            return HttpResponseForbidden()

        # If UserNotFound: 404 Not Found
        user = user_backend.get(username=name)

        property_backend.set_multiple(user=user,
                                      props=get_freeform_dict(request))
        return HttpResponseNoContent()


class UserPropHandler(RestAuthSubResourceView):
    """
    Handle requests to ``/users/<user>/props/<prop>/``.
    """
    log = logging.getLogger('users.user.props.prop')
    http_method_names = ['get', 'put', 'delete']

    def get(self, request, largs, name, subname):
        """
        Get value of a single property.
        """
        if not request.user.has_perm('Users.prop_get'):
            return HttpResponseForbidden()

        # If UserNotFound: 404 Not Found
        user = user_backend.get(username=name)

        value = property_backend.get(user=user, key=subname)

        return HttpRestAuthResponse(request, value)

    def put(self, request, largs, name, subname):
        """
        Set value of a single property.
        """
        if not request.user.has_perm('Users.prop_set'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        value = get_dict(request, [u'value'])

        # If UserNotFound: 404 Not Found
        user = user_backend.get(username=name)

        key, old_value = property_backend.set(user=user, key=subname,
                                              value=value)

        if old_value is None:  # new property
            self.log.info('Set to "%s"', value, extra=largs)
            return HttpResponseCreated(request, 'users.user.props.prop',
                                       name=name, subname=key)
        else:  # existing property
            self.log.info('Changed from "%s" to "%s"',
                          old_value, value, extra=largs)
            return HttpRestAuthResponse(request, old_value)

    def delete(self, request, largs, name, subname):
        """
        Delete a property.
        """
        if not request.user.has_perm('Users.prop_delete'):
            return HttpResponseForbidden()

        # If UserNotFound: 404 Not Found
        user = user_backend.get(username=name)

        property_backend.remove(user=user, key=subname)
        return HttpResponseNoContent()
