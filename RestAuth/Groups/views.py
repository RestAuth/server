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

"""This module implements all HTTP queries to ``/group/*``."""

from __future__ import unicode_literals

import logging

from django.http import HttpResponseForbidden
from django.utils import six

from RestAuthCommon.strprep import stringcheck
from RestAuthCommon.strprep import stringprep

from backends import backend
from backends import group_backend
from common.errors import UserNotFound
from common.errors import GroupNotFound
from common.responses import HttpResponseCreated
from common.responses import HttpResponseNoContent
from common.responses import HttpRestAuthResponse
from common.views import RestAuthView
from common.views import RestAuthResourceView
from common.views import RestAuthSubResourceView


class GroupsView(RestAuthView):
    """Handle requests to ``/groups/``."""

    log = logging.getLogger('groups')
    http_method_names = ['get', 'post', 'put', ]
    post_required = (('group', six.string_types),)
    post_optional = (
        ('users', list),
    )
    put_required = (
        ('groups', list),
        ('user', six.string_types),
    )

    def get(self, request, largs):
        """Get a list of groups or a list of groups where the user is a member of."""

        username = request.GET.get('user', None)
        if username is None or username == '':
            if not request.user.has_perm('Groups.groups_list'):
                return HttpResponseForbidden()

            groups = group_backend.list(service=request.user)
        else:
            if not request.user.has_perm('Groups.groups_for_user'):
                return HttpResponseForbidden()

            # Get all groups of a user
            user = backend.get(username=stringprep(username))
            groups = group_backend.list(service=request.user, user=user)

        groups = [g.lower() for g in groups]
        return HttpRestAuthResponse(request, groups)

    def parse_users(self, usernames):
        users = []
        for username in [stringprep(u) for u in usernames]:
            try:
                users.append(backend.get(username))
            except UserNotFound:
                pass
        return users

    def parse_groups(self, groupnames, service, dry=False, transaction=True):
        groups = []
        for groupname in [stringprep(u) for u in groupnames]:
            try:
                groups.append(backend.get(groupname))
            except UserNotFound:
                groups.append(
                    group_backend.create(groupname, service=service, dry=dry, transaction=False))
        return groups

    def post(self, request, largs, dry=False):
        """Create a new group."""

        if not request.user.has_perm('Groups.group_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        name, users = self._parse_post(request)
        name = stringcheck(name)

        if users is not None:
            users = self.parse_users(users)

        # If ResourceExists: 409 Conflict
        group = group_backend.create(service=request.user, name=name, users=users, dry=dry)

        self.log.info('%s: Created group', group.name, extra=largs)
        return HttpResponseCreated()  # Created

    def put(self, request, largs):
        """Set groups of a user."""

        if not request.user.has_perms(['Groups.group_remove_user', 'Groups.group_add_user']):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        groupnames, username = self._parse_put(request)

        # If PreconditionFailed: 412 Precondition Failed
        user = backend.get(username=stringprep(username))
        groupnames = [stringprep(g) for g in groupnames]

        group_backend.set_groups_for_user(service=request.user, user=user, groupnames=groupnames)
        return HttpResponseNoContent()

class GroupHandlerView(RestAuthResourceView):
    """Handle requests to ``/groups/<group>/``."""

    log = logging.getLogger('groups.group')
    http_method_names = ['get', 'delete']

    def get(self, request, largs, name):
        """Verify that a group exists."""

        if not request.user.has_perm('Groups.group_exists'):
            return HttpResponseForbidden()

        if group_backend.exists(service=request.user, name=name):
            return HttpResponseNoContent()
        else:
            raise GroupNotFound(name)

    def delete(self, request, largs, name):
        """Delete a group."""

        if not request.user.has_perm('Groups.group_delete'):
            return HttpResponseForbidden()

        group = group_backend.get(service=request.user, name=name)
        group_backend.remove(group=group)
        self.log.info("Deleted group", extra=largs)
        return HttpResponseNoContent()


class GroupUsersIndex(RestAuthResourceView):
    """Handle requests to ``/groups/<group>/users/``."""

    log = logging.getLogger('groups.group.users')
    http_method_names = ['get', 'post', 'put', ]
    post_required = (('user', six.string_types), )
    put_required = (('users', list),)

    def get(self, request, largs, name):
        """Get all users in a group."""

        if not request.user.has_perm('Groups.group_users'):
            return HttpResponseForbidden()

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)

        users = group_backend.members(group=group)
        return HttpRestAuthResponse(request, users)

    def post(self, request, largs, name):
        """Add a user to a group."""

        if not request.user.has_perm('Groups.group_add_user'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        username = stringprep(self._parse_post(request))

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)

        # If UserNotFound: 404 Not Found
        user = backend.get(username=username)

        group_backend.add_user(group=group, user=user)

        self.log.info('Add user "%s"', username, extra=largs)
        return HttpResponseNoContent()

    def put(self, request, largs, name):
        """Set users of a group."""

        if not request.user.has_perms(['Groups.group_add_user', 'Groups.group_remove_user']):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        users = [stringprep(u) for u in self._parse_put(request)]

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)

        # If UserNotFound: 404 Not Found
        users = [backend.get(u) for u in users]

        group_backend.set_users_for_group(group=group, users=users)

        self.log.info('Set users for group "%s"', name, extra=largs)
        return HttpResponseNoContent()


class GroupUserHandler(RestAuthSubResourceView):
    """Handle requests to ``/groups/<group>/users/<user>/``."""

    log = logging.getLogger('groups.group.users.user')
    http_method_names = ['get', 'delete']

    def get(self, request, largs, name, subname):
        """Verify that a user is in a group."""

        if not request.user.has_perm('Groups.group_user_in_group'):
            return HttpResponseForbidden()

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)

        # If UserNotFound: 404 Not Found
        user = backend.get(username=subname)

        if group_backend.is_member(group=group, user=user):
            return HttpResponseNoContent()
        else:
            raise UserNotFound(subname)  # 404 Not Found

    def delete(self, request, largs, name, subname):
        """Remove a user from a group."""

        if not request.user.has_perm('Groups.group_remove_user'):
            return HttpResponseForbidden()

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)

        # If UserNotFound: 404 Not Found
        user = backend.get(username=subname)

        group_backend.rm_user(group=group, user=user)
        self.log.info('Remove user from group', extra=largs)
        return HttpResponseNoContent()


class GroupGroupsIndex(RestAuthResourceView):
    """Handle requests to ``/groups/<group>/group/``."""

    log = logging.getLogger('groups.group.groups')
    http_method_names = ['get', 'post', 'put', ]
    post_required = (('group', six.string_types),)
    put_required = (
        ('groups', list),
    )

    def get(self, request, largs, name):
        """Get a list of sub-groups."""

        if not request.user.has_perm('Groups.group_groups_list'):
            return HttpResponseForbidden()

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)

        groups = group_backend.subgroups(group=group)
        return HttpRestAuthResponse(request, groups)

    def post(self, request, largs, name):
        """Add a sub-group."""

        if not request.user.has_perm('Groups.group_add_group'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        subname = stringprep(self._parse_post(request))

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)
        subgroup = group_backend.get(service=request.user, name=subname)

        group_backend.add_subgroup(group=group, subgroup=subgroup)

        self.log.info('Add subgroup "%s"', subname, extra=largs)
        return HttpResponseNoContent()

    def put(self, request, largs, name):
        """Set the sub-groups of a group."""

        if not request.user.has_perms(['Groups.group_add_group', 'Groups.group_remove_group']):
            return HttpResponseForbidden()

        subnames = [stringprep(g) for g in self._parse_put(request)]

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)
        subgroups = [group_backend.get(service=request.user, name=n) for n in subnames]

        group_backend.set_subgroups(group=group, subgroups=subgroups)

        self.log.info('Set sub-groups', extra=largs)
        return HttpResponseNoContent()


class GroupGroupHandler(RestAuthSubResourceView):
    """Handle requests to ``/groups/<meta-group>/group/<sub-group>/``."""

    log = logging.getLogger('groups.group.groups.subgroup')
    http_method_names = ['get', 'delete']

    def get(self, request, largs, name, subname):
        if not request.user.has_perm('Groups.group_groups_list'):
            return HttpResponseForbidden()

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)
        subgroup = group_backend.get(service=request.user, name=subname)
        if group_backend.has_subgroup(group, subgroup):
            return HttpResponseNoContent()
        else:
            raise GroupNotFound(name)

    def delete(self, request, largs, name, subname):
        """Remove a subgroup from a group."""

        if not request.user.has_perm('Groups.group_remove_group'):
            return HttpResponseForbidden()

        # If GroupNotFound: 404 Not Found
        group = group_backend.get(service=request.user, name=name)
        subgroup = group_backend.get(service=request.user, name=subname)

        group_backend.rm_subgroup(group=group, subgroup=subgroup)
        self.log.info('Remove subgroup %s', subname, extra=largs)
        return HttpResponseNoContent()
