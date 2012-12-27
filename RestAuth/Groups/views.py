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
This module implements all HTTP queries to ``/group/*``.
"""

import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden

from RestAuth.Users.models import ServiceUser
from RestAuth.Groups.models import Group, group_create
from RestAuth.common.errors import GroupExists
from RestAuth.common.utils import import_path
from RestAuth.common.types import get_dict
from RestAuth.common.responses import *
from RestAuth.common.views import (RestAuthView, RestAuthResourceView,
                                   RestAuthSubResourceView)

group_backend = import_path(getattr(
            settings, 'PROPERTY_BACKEND',
            'RestAuth.backends.django_orm.DjangoGroupBackend'
))[0]()


class GroupsView(RestAuthView):
    """
    Handle requests to ``/groups/``.
    """
    log = logging.getLogger('groups')
    http_method_names = ['get', 'post']

    def get(self, request, largs):
        """
        Get a list of groups or, if called with the 'user' query parameter,
        a list of groups where the user is a member of.
        """
        if 'user' in request.GET:
            if not request.user.has_perm('Groups.groups_for_user'):
                return HttpResponseForbidden()

            # Get all groups of a user
            username = request.GET['user'].lower()

            # If User.DoesNotExist: 404 Not Found
            user = ServiceUser.objects.only('id').get(username=username)

            groups = Group.objects.member(user=user, service=request.user)
            groups = list(groups.only('id').values_list('name', flat=True))

            self.log.debug('Get groups for user %s',
                           username, extra=largs)
            return HttpRestAuthResponse(request, groups)
        else:  # Get a list of groups:
            if not request.user.has_perm('Groups.groups_list'):
                return HttpResponseForbidden()

            # get all groups for this service
            groups = Group.objects.filter(service=request.user)
            groups = list(groups.only('name').values_list('name', flat=True))

            self.log.debug('Get all groups', extra=largs)
            return HttpRestAuthResponse(request, groups)

    def post(self, request, largs):
        """
        Create a new group.
        """
        if not request.user.has_perm('Groups.group_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        groupname = get_dict(request, [u'group'])

        # If ResourceExists: 409 Conflict
        group = group_create(groupname, request.user)

        self.log.info('%s: Created group', groupname, extra=largs)
        return HttpResponseCreated(request, group)  # Created


class GroupHandlerView(RestAuthResourceView):
    """
    Handle requests to ``/groups/<group>/``.
    """
    log = logging.getLogger('groups.group')
    http_method_names = ['get', 'delete']

    def get(self, request, largs, name):
        """
        Verify that a group exists.
        """
        if not request.user.has_perm('Groups.group_exists'):
            return HttpResponseForbidden()

        self.log.debug("Check if group exists", extra=largs)
        if Group.objects.filter(name=name, service=request.user).exists():
            return HttpResponseNoContent()
        else:
            raise Group.DoesNotExist

    def delete(self, request, largs, name):
        """
        Delete a group.
        """
        if not request.user.has_perm('Groups.group_delete'):
            return HttpResponseForbidden()

        self.log.info("Deleted group", extra=largs)
        if Group.objects.filter(name=name, service=request.user).exists():
            Group.objects.filter(name=name, service=request.user).delete()
            return HttpResponseNoContent()
        else:
            raise Group.DoesNotExist


class GroupUsersIndex(RestAuthResourceView):
    """
    Handle requests to ``/groups/<group>/users/``.
    """
    log = logging.getLogger('groups.group.users')
    http_method_names = ['get', 'post']

    def get(self, request, largs, name):
        """
        Get all users in a group.
        """
        if not request.user.has_perm('Groups.group_users'):
            return HttpResponseForbidden()

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('id').get(name=name, service=request.user)

        users = group.get_members().values_list('username', flat=True)

        # If MarshalError: 500 Internal Server Error
        self.log.debug("Get users in group", extra=largs)
        return HttpRestAuthResponse(request, list(users))

    def post(self, request, largs, name):
        """
        Add a user to a group.
        """
        if not request.user.has_perm('Groups.group_add_user'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        username = get_dict(request, [u'user'])

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('id').get(name=name, service=request.user)

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('id').get(username=username)

        group.users.add(user)

        self.log.info('Add user "%s"', username, extra=largs)
        return HttpResponseNoContent()


class GroupUserHandler(RestAuthSubResourceView):
    """
    Handle requests to ``/groups/<group>/users/<user>/``.
    """
    log = logging.getLogger('groups.group.users.user')
    http_method_names = ['get', 'delete']

    def get(self, request, largs, name, subname):
        """
        Verify that a user is in a group.
        """
        if not request.user.has_perm('Groups.group_user_in_group'):
            return HttpResponseForbidden()

        self.log.debug('Check if user is in group', extra=largs)

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('id').get(name=name, service=request.user)

        if group.is_member(subname):
            return HttpResponseNoContent()
        else:
            raise ServiceUser.DoesNotExist()  # 404 Not Found

    def delete(self, request, largs, name, subname):
        """
        Remove a user from a group.
        """
        if not request.user.has_perm('Groups.group_remove_user'):
            return HttpResponseForbidden()

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('id').get(name=name, service=request.user)

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('id').get(username=subname)

        if group.is_member(user):
            group.users.remove(user)
            self.log.info('Remove user from group', extra=largs)
            return HttpResponseNoContent()
        else:
            raise ServiceUser.DoesNotExist()  # 404 Not Found


class GroupGroupsIndex(RestAuthResourceView):
    """
    Handle requests to ``/groups/<group>/group/``.
    """
    log = logging.getLogger('groups.group.groups')
    http_method_names = ['get', 'post']

    def get(self, request, largs, name):
        """
        Get a list of sub-groups
        """
        if not request.user.has_perm('Groups.group_groups_list'):
            return HttpResponseForbidden()

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('id').get(name=name, service=request.user)

        groups = group.groups.filter(service=request.user).values_list(
            'name', flat=True)

        # If MarshalError: 500 Internal Server Error
        self.log.debug('Get subgroups', extra=largs)
        return HttpRestAuthResponse(request, list(groups))

    def post(self, request, largs, name):
        """
        Add a sub-group.
        """
        if not request.user.has_perm('Groups.group_add_group'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        subname = get_dict(request, [u'group'])

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('id').get(name=name, service=request.user)
        sub_group = Group.objects.only('id').get(
            name=subname, service=request.user)

        group.groups.add(sub_group)
        self.log.info('Add subgroup "%s"', subname, extra=largs)
        return HttpResponseNoContent()


class GroupGroupHandler(RestAuthSubResourceView):
    """
    Handle requests to ``/groups/<meta-group>/group/<sub-group>/``.
    """
    log = logging.getLogger('groups.group.groups.subgroup')
    http_method_names = ['delete']

    def delete(self, request, largs, name, subname):
        """
        Remove a subgroup from a group.
        """
        if not request.user.has_perm('Groups.group_remove_group'):
            return HttpResponseForbidden()

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('id').get(name=name, service=request.user)
        subgroup = Group.objects.only('id').get(
            name=subname, service=request.user)

        qs = group.groups.filter(name=subname, service=request.user)
        if not qs.exists():
            raise Group.DoesNotExist()

        group.groups.remove(subgroup)
        self.log.info('Remove subgroup %s', subname, extra=largs)
        return HttpResponseNoContent()
