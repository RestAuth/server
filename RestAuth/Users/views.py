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

import logging
from datetime import datetime

from django.http import HttpResponseForbidden

from RestAuthCommon.error import BadRequest
from RestAuth.Users.models import ServiceUser, Property, user_create
from RestAuth.common.types import get_dict, get_freeform_dict
from RestAuth.common.responses import *
from RestAuth.common.views import (RestAuthView, RestAuthResourceView,
                                   RestAuthSubResourceView)

from RestAuth.common.decorators import sql_profile


class UsersView(RestAuthView):
    """
    Handle requests to /users/.
    """
    http_method_names = ['get', 'post']
    log = logging.getLogger('users')

    def get(self, request, largs, *args, **kwargs):
        if not request.user.has_perm('Users.users_list'):
            return HttpResponseForbidden()

        names = ServiceUser.objects.values_list('username', flat=True)

        self.log.debug("Got list of users", extra=largs)
        return HttpRestAuthResponse(request, list(names))

    def post(self, request, largs, *args, **kwargs):
        if not request.user.has_perm('Users.user_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        name, password, props = get_dict(
            request, [u'user'], [u'password', u'properties'])

        # If ResourceExists: 409 Conflict
        # If UsernameInvalid: 412 Precondition Failed
        # If PasswordInvalid: 412 Precondition Failed
        user = user_create(name, password)
        if props:
            if props.__class__ != dict:
                raise BadRequest('Properties not a dictionary!')
            [user.set_property(key, value) for key, value in props.iteritems()]

        if not props or 'date joined' not in props:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user.set_property('date joined', stamp)

        self.log.info('%s: Created user', name, extra=largs)
        return HttpResponseCreated(request, user)


class UserHandlerView(RestAuthResourceView):
    """
    Handle requests to /users/<user>/.
    """
    http_method_names = ['get', 'post', 'put', 'delete']
    log = logging.getLogger('users.user')

    def get(self, request, largs, name):
        if not request.user.has_perm('Users.user_exists'):
            return HttpResponseForbidden()

        self.log.debug("Check if user exists", extra=largs)
        if ServiceUser.objects.filter(username=name).exists():
            return HttpResponseNoContent()
        else:
            raise ServiceUser.DoesNotExist()

    def post(self, request, largs, name):
        if not request.user.has_perm('Users.user_verify_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password = get_dict(request, [u'password'])

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('password').get(username=name)

        if not user.check_password(password):
            # password does not match - raises 404
            self.log.info("Wrong password checked", extra=largs)
            raise ServiceUser.DoesNotExist("Password invalid for this user.")
        user.save()  # update "modified" timestamp, perhaps hash

        self.log.debug("Checked password (ok)", extra=largs)
        return HttpResponseNoContent()  # Ok

    def put(self, request, largs, name):
        if not request.user.has_perm('Users.user_change_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password, = get_dict(request, optional=[u'password'])

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=name)

        # If UsernameInvalid: 412 Precondition Failed
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

        self.log.info("Updated password", extra=largs)
        return HttpResponseNoContent()

    def delete(self, request, largs, name):
        if not request.user.has_perm('Users.user_delete'):
            return HttpResponseForbidden()

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=name)

        user.delete()

        self.log.info("Deleted user", extra=largs)
        return HttpResponseNoContent()


class UserPropsIndex(RestAuthResourceView):
    """
    Handle requests to /users/<user>/props/.
    """
    log = logging.getLogger('users.user.props')
    http_method_names = ['get', 'post', 'put']

    def get(self, request, largs, name):
        if not request.user.has_perm('Users.props_list'):
            return HttpResponseForbidden()

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=name)
        props = user.get_properties()

        self.log.debug("Got properties", extra=largs)
        return HttpRestAuthResponse(request, props)

    def post(self, request, largs, name):
        if not request.user.has_perm('Users.prop_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        prop, value = get_dict(request, [u'prop', u'value'])

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=name)

        # If PropertyExists: 409 Conflict
        property = user.add_property(prop, value)

        self.log.info(
            'Created property "%s" as "%s"', prop, value, extra=largs)
        return HttpResponseCreated(request, property)

    def put(self, request, largs, name):
        if not request.user.has_perm('Users.prop_create'):
            return HttpResponseForbidden()

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=name)

        for key, value in get_freeform_dict(request).iteritems():
            user.set_property(key, value)
        return HttpResponseNoContent()


class UserPropHandler(RestAuthSubResourceView):
    """
    Handle requests to /users/<user>/props/<prop>/.
    """
    log = logging.getLogger('users.user.props.prop')
    http_method_names = ['get', 'put', 'delete']

    def get(self, request, largs, name, subname):
        if not request.user.has_perm('Users.prop_get'):
            return HttpResponseForbidden()

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=name)

        # If Property.DoesNotExist: 404 Not Found
        prop = user.get_property(subname)

        self.log.debug('Got property', extra=largs)
        return HttpRestAuthResponse(request, prop.value)

    def put(self, request, largs, name, subname):
        if not request.user.has_perm('Users.prop_set'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        value = get_dict(request, [u'value'])

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=name)

        prop, old_value = user.set_property(subname, value)
        if old_value is None:  # new property
            self.log.info('Set to "%s"', value, extra=largs)
            return HttpResponseCreated(request, prop)
        else:  # existing property
            self.log.info('Changed from "%s" to "%s"',
                          old_value, value, extra=largs)
            return HttpRestAuthResponse(request, old_value)

    def delete(self, request, largs, name, subname):
        if not request.user.has_perm('Users.prop_delete'):
            return HttpResponseForbidden()

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=name)

        # If Property.DoesNotExist: 404 Not Found
        user.del_property(subname)

        self.log.info('Delete property', extra=largs)
        return HttpResponseNoContent()
