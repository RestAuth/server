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

from django.http import HttpResponse, HttpResponseForbidden

from RestAuth.Services.decorator import login_required
from RestAuth.Users.models import *
from RestAuth.Groups.models import *
from RestAuth.common.errors import GroupExists
from RestAuth.common.types import get_dict
from RestAuth.common.responses import *
from RestAuth.common.views import RestAuthView, RestAuthResourceView


class GroupsView(RestAuthView):
    log = logging.getLogger('groups')
    http_method_names = ['get', 'post']

    def get(self, request):
        if 'user' in request.GET:
            if not request.user.has_perm('Groups.groups_for_user'):
                return HttpResponseForbidden()

            # Get all groups of a user
            username = request.GET['user'].lower()

            # If User.DoesNotExist: 404 Not Found
            user = ServiceUser.objects.only('username').get(username=username)

            groups = user.get_groups(request.user)
            names = [group.name for group in groups]

            self.log.debug('Get groups for user %s',
                           username, extra=self.largs)
            return HttpRestAuthResponse(request, names)
        else:  # Get a list of groups:
            if not request.user.has_perm('Groups.groups_list'):
                return HttpResponseForbidden()

            # get all groups for this service
            groups = Group.objects.filter(service=request.user)
            groups = list(groups.values_list('name', flat=True))

            self.log.debug('Get all groups', extra=self.largs)
            return HttpRestAuthResponse(request, groups)

    def post(self, request):
        if not request.user.has_perm('Groups.group_create'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        groupname = get_dict(request, [u'group'])

        # If ResourceExists: 409 Conflict
        group = group_create(groupname, request.user)

        self.log.info('%s: Created group', groupname, extra=self.largs)
        return HttpResponseCreated(request, group)  # Created


class GroupHandlerView(RestAuthResourceView):
    log = logging.getLogger('groups.group')
    http_method_names = ['get', 'delete']

    def get(self, request, name):  # Verify that a group exists
        if not request.user.has_perm('Groups.group_exists'):
            return HttpResponseForbidden()

        group = Group.objects.only('name').get(
            name=name, service=request.user)

        self.log.debug("Check if group exists", extra=self.largs)
        return HttpResponseNoContent()

    def delete(self, request, name):  # Delete group
        if not request.user.has_perm('Groups.group_delete'):
            return HttpResponseForbidden()

        group = Group.objects.only('name').get(
            name=name, service=request.user)

        group.delete()
        self.log.info("Deleted group", extra=self.largs)
        return HttpResponseNoContent()  # OK


class GroupUsersIndex(RestAuthResourceView):
    log = logging.getLogger('groups.group.users')
    http_method_names = ['get', 'post']

    def get(self, request, name):  # Get all users in a group
        if not request.user.has_perm('Groups.group_users'):
            return HttpResponseForbidden()

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('name').get(name=name, service=request.user)

        users = group.get_members()

        # If MarshalError: 500 Internal Server Error
        self.log.debug("Get users in group", extra=self.largs)
        return HttpRestAuthResponse(request, list(users))

    def post(self, request, name):  # Add a user to a group
        if not request.user.has_perm('Groups.group_add_user'):
            return HttpResponseForbidden()

        # If BadRequest: 400 Bad Request
        username = get_dict(request, [u'user'])

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('name').get(name=name, service=request.user)

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=username)

        group.users.add(user)

        self.log.info('Add user "%s"', username, extra=self.largs)
        return HttpResponseNoContent()


class GroupUserHandler(RestAuthResourceView):
    log = logging.getLogger('groups.group.users.user')
    http_method_names = ['get', 'delete']

    def dispatch(self, request, *args, **kwargs):
        kwargs['username'] = kwargs.get('username').lower()
        return super(GroupUserHandler, self).dispatch(
            request, largs={'user': kwargs.get('username')}, **kwargs)

    def get(self, request, name, username):  # Verify that a user is in a group
        if not request.user.has_perm('Groups.group_user_in_group'):
            return HttpResponseForbidden()

        self.log.debug('Check if user is in group', extra=self.largs)

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('name').get(name=name, service=request.user)

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=username)

        if group.is_member(user):
            return HttpResponseNoContent()
        else:
            raise ServiceUser.DoesNotExist()  # 404 Not Found

    def delete(self, request, name, username):  # Remove user from a group
        if not request.user.has_perm('Groups.group_remove_user'):
            return HttpResponseForbidden()

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('name').get(name=name, service=request.user)

        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=username)

        if not group.is_member(user, False):
            raise User.DoesNotExist()  # 404 Not Found

        group.users.remove(user)
        self.log.info('Remove user from group', extra=self.largs)
        return HttpResponseNoContent()


class GroupGroupsIndex(RestAuthResourceView):
    log = logging.getLogger('groups.group.groups')
    http_method_names = ['get', 'post']

    def get(self, request, name):  # get a list of sub-groups
        if not request.user.has_perm('Groups.group_groups_list'):
            return HttpResponseForbidden()

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('name').get(name=name, service=request.user)

        groups = group.groups.filter(service=request.user).values_list(
            'name', flat=True)

        # If MarshalError: 500 Internal Server Error
        self.log.debug('Get subgroups', extra=self.largs)
        return HttpRestAuthResponse(request, list(groups))

    def post(self, request, name):  # Add a sub-group:
        if not request.user.has_perm('Groups.group_add_group'):
            return HttpResponseForbidden()

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('name').get(name=name, service=request.user)

        # If BadRequest: 400 Bad Request
        sub_groupname = get_dict(request, [u'group'])

        # If Group.DoesNotExist: 404 Not Found
        sub_group = Group.objects.only('name').get(
            name=sub_groupname, service=request.user)

        group.groups.add(sub_group)
        self.log.info('Add subgroup "%s"', sub_groupname, extra=self.largs)
        return HttpResponseNoContent()


class GroupGroupHandler(RestAuthResourceView):
    log = logging.getLogger('groups.group.groups.subgroup')
    http_method_names = ['delete']

    def dispatch(self, request, *args, **kwargs):
        kwargs['subgroupname'] = kwargs.get('subgroupname').lower()
        return super(GroupGroupHandler, self).dispatch(
            request, largs={'subgroup': kwargs.get('subgroupname')}, **kwargs)

    def delete(self, request, name, subgroupname):  # Remove group from a group
        if not request.user.has_perm('Groups.group_remove_group'):
            return HttpResponseForbidden()

        # If Group.DoesNotExist: 404 Not Found
        group = Group.objects.only('name').get(
            name=name, service=request.user)
        # If Group.DoesNotExist: 404 Not Found
        subgroup = Group.objects.only('name').get(
            name=subgroupname, service=request.user)

        qs = group.groups.filter(name=subgroupname, service=request.user)
        if not qs.exists():
            raise Group.DoesNotExist()

        group.groups.remove(subgroup)
        self.log.info('Remove subgroup %s', subgroupname, extra=self.largs)
        return HttpResponseNoContent()
