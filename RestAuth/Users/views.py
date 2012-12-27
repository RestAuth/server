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
from datetime import datetime

from django.conf import settings
from django.http import HttpResponseForbidden

from RestAuthCommon.error import BadRequest
from RestAuth.Users.models import ServiceUser, user_create, validate_username
from RestAuth.common.types import get_dict, get_freeform_dict
from RestAuth.common.responses import *
from RestAuth.common.utils import import_path
from RestAuth.common.views import (RestAuthView, RestAuthResourceView,
                                   RestAuthSubResourceView)

from RestAuth.common.decorators import sql_profile

user_backend = import_path(getattr(
    settings, 'USER_BACKEND',
    'RestAuth.backends.django_orm.DjangoUserBackend'
))[0]()
property_backend = import_path(getattr(
    settings, 'PROPERTY_BACKEND',
    'RestAuth.backends.django_orm.DjangoPropertyBackend'
))[0]()


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

    def post(self, request, largs, *args, **kwargs):
        """
        Create a new user.
        """
        if not request.user.has_perm('Users.user_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        name, password, props = get_dict(
            request, [u'user'], [u'password', u'properties'])

        # If UsernameInvalid: 412 Precondition Failed
        validate_username(name)

        # If ResourceExists: 409 Conflict
        # If PasswordInvalid: 412 Precondition Failed
        user = user_backend.create(name, password, props, dry=False)

        self.log.info('%s: Created user', name, extra=largs)
        return HttpResponseCreated(request, user)


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

        if user_backend.exists(name):
            return HttpResponseNoContent()
        else:
            raise ServiceUser.DoesNotExist()

    def post(self, request, largs, name):
        """
        Verify a users password.
        """
        if not request.user.has_perm('Users.user_verify_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password = get_dict(request, [u'password'])

        if user_backend.check_password(name, password):
            return HttpResponseNoContent()
        else:
            return HttpResponseResourceNotFound('user')

    def put(self, request, largs, name):
        """
        Change a users password.
        """
        if not request.user.has_perm('Users.user_change_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password, = get_dict(request, optional=[u'password'])

        user_backend.set_password(name, password)
        return HttpResponseNoContent()

    def delete(self, request, largs, name):
        """
        Delete a user.
        """
        if not request.user.has_perm('Users.user_delete'):
            return HttpResponseForbidden()

        # If User.DoesNotExist: 404 Not Found
        user_backend.remove(name)
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

        # If User.DoesNotExist: 404 Not Found
        props = property_backend.list(name)
        return HttpRestAuthResponse(request, props)

    def post(self, request, largs, name):
        """
        Create a new property.
        """
        if not request.user.has_perm('Users.prop_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        prop, value = get_dict(request, [u'prop', u'value'])

        # If User.DoesNotExist: 404 Not Found
        # If PropertyExists: 409 Conflict
        property = property_backend.create(name, prop, value)

        self.log.info(
            'Created property "%s" as "%s"', prop, value, extra=largs)
        return HttpResponseCreated(request, property)

    def put(self, request, largs, name):
        """
        Set multiple properties.
        """
        if not request.user.has_perm('Users.prop_create'):
            return HttpResponseForbidden()

        # If User.DoesNotExist: 404 Not Found
        property_backend.set_multiple(name, get_freeform_dict(request))
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

        # If User.DoesNotExist: 404 Not Found
        # If Property.DoesNotExist: 404 Not Found
        value = property_backend.get(name, subname)

        return HttpRestAuthResponse(request, value)

    def put(self, request, largs, name, subname):
        """
        Set value of a single property.
        """
        if not request.user.has_perm('Users.prop_set'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        value = get_dict(request, [u'value'])

        # If User.DoesNotExist: 404 Not Found
        prop, old_value = property_backend.set(name, subname, value)

        if old_value is None:  # new property
            self.log.info('Set to "%s"', value, extra=largs)
            return HttpResponseCreated(request, prop)
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

        # If User.DoesNotExist: 404 Not Found
        # If Property.DoesNotExist: 404 Not Found
        property_backend.remove(name, subname)
        return HttpResponseNoContent()
