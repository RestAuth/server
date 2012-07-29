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

import httplib
import logging

from django.http import HttpResponseForbidden

from RestAuthCommon.error import BadRequest
from RestAuth.Services.decorator import login_required
from RestAuth.Users.models import *
from RestAuth.common.types import get_dict
from RestAuth.common.responses import *

from RestAuth.common.decorators import sql_profile


@login_required(realm="/users/")
def index(request):
    service = request.user.username
    logger = logging.getLogger('users')
    log_args = {'service': service}

    if request.method == "GET":  # get list of users:
        if not request.user.has_perm('Users.users_list'):
            return HttpResponseForbidden()

        names = ServiceUser.objects.values_list('username', flat=True)

        logger.debug("Got list of users", extra=log_args)
        return HttpRestAuthResponse(request, list(names))
    elif request.method == 'POST':  # create new user:
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

        logger.info('%s: Created user', name, extra=log_args)
        return HttpResponseCreated(request, user)
    else:  # pragma: no cover
        logger.error('Method not allowed: %s', request.method, extra=log_args)
        return HttpResponse(status=405)


@login_required(realm="/users/<user>/")
def user_handler(request, username):
    service = request.user.username
    username = username.lower()
    logger = logging.getLogger('users.user')
    log_args = {'service': service, 'username': username}

    if request.method == 'GET':  # Verify that a user exists:
        if not request.user.has_perm('Users.user_exists'):
            return HttpResponseForbidden()

        logger.debug("Check if user exists", extra=log_args)
        if ServiceUser.objects.filter(username=username).exists():
            return HttpResponseNoContent()  # OK
        else:
            raise ServiceUser.DoesNotExist()
    elif request.method == 'POST':  # verify password
        if not request.user.has_perm('Users.user_verify_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password = get_dict(request, [u'password'])

        # If User.DoesNotExist: 404 Not Found
        fields = ['username', 'algorithm', 'salt', 'hash']
        user = ServiceUser.objects.only(*fields).get(username=username)

        if not user.check_password(password):
            # password does not match - raises 404
            logger.info("Wrong password checked", extra=log_args)
            raise ServiceUser.DoesNotExist("Password invalid for this user.")
        user.save()  # update "modified" timestamp, perhaps hash

        logger.debug("Checked password (ok)", extra=log_args)
        return HttpResponseNoContent()  # Ok
    elif request.method == 'PUT':  # Change password
        if not request.user.has_perm('Users.user_change_password'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        password, = get_dict(request, optional=[u'password'])

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=username)

        # If UsernameInvalid: 412 Precondition Failed
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

        logger.info("Updated password", extra=log_args)
        return HttpResponseNoContent()
    elif request.method == 'DELETE':  # delete a user:
        if not request.user.has_perm('Users.user_delete'):
            return HttpResponseForbidden()

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=username)

        user.delete()

        logger.info("Deleted user", extra=log_args)
        return HttpResponseNoContent()
    else:  # pragma: no cover
        logger.error('Method not allowed: %s', request.method, extra=log_args)
        return HttpResponse(status=405)  # Method Not Allowed


@login_required(realm="/users/<user>/props/")
def userprops_index(request, username):
    service = request.user.username
    username = username.lower()
    # If User.DoesNotExist: 404 Not Found
    user = ServiceUser.objects.only('username').get(username=username)

    logger = logging.getLogger('users.user.props')
    log_args = {'service': service, 'username': username}

    if request.method == 'GET':  # get all properties
        if not request.user.has_perm('Users.props_list'):
            return HttpResponseForbidden()

        props = user.get_properties()

        logger.debug("Got properties", extra=log_args)
        return HttpRestAuthResponse(request, props)
    elif request.method == 'POST':  # create property
        if not request.user.has_perm('Users.prop_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        prop, value = get_dict(request, [u'prop', u'value'])

        # If PropertyExists: 409 Conflict
        property = user.add_property(prop, value)

        logger.info(
            'Created property "%s" as "%s"', prop, value, extra=log_args)
        return HttpResponseCreated(request, property)
    else:  # pragma: no cover
        logger.error('Method not allowed: %s', request.method, extra=log_args)
        return HttpResponse(status=405)  # Method Not Allowed


@login_required(realm="/users/<user>/props/<prop>/")
def userprops_prop(request, username, prop):
    service = request.user.username
    username = username.lower()
    # If User.DoesNotExist: 404 Not Found
    user = ServiceUser.objects.only('username').get(username=username)

    logger = logging.getLogger('users.user.props.prop')
    log_args = {'service': service, 'username': username, 'prop': prop}

    if request.method == 'GET':  # get value of a property
        if not request.user.has_perm('Users.prop_get'):
            return HttpResponseForbidden()

        # If Property.DoesNotExist: 404 Not Found
        prop = user.get_property(prop)

        logger.debug('Got property', extra=log_args)
        return HttpRestAuthResponse(request, prop.value)

    elif request.method == 'PUT':  # Set property
        if not request.user.has_perm('Users.prop_set'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        value = get_dict(request, [u'value'])

        prop, old_value = user.set_property(prop, value)
        if old_value.__class__ == unicode:  # property previously defined:
            logger.info(
                'Changed from "%s" to "%s"', old_value, value, extra=log_args)
            return HttpRestAuthResponse(request, old_value)
        else:  # new property:
            logger.info('Set to "%s"', value, extra=log_args)
            return HttpResponseCreated(request, prop)

    elif request.method == 'DELETE':  # Delete property:
        if not request.user.has_perm('Users.prop_delete'):
            return HttpResponseForbidden()

        # If Property.DoesNotExist: 404 Not Found
        user.del_property(prop)

        logger.info('Delete property', extra=log_args)
        return HttpResponseNoContent()
    else:  # pragma: no cover
        logger.error('Method not allowed: %s', request.method, extra=log_args)
        return HttpResponse(status=405)  # Method Not Allowed
