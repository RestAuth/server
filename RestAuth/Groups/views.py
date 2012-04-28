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

@login_required(realm='/groups/')
#@sql_profile()
def index(request):
    service = request.user
    logger = logging.getLogger('groups')
    log_args = { 'service': service }

    if request.method == 'GET' and 'user' in request.GET:
        if not request.user.has_perm('Groups.groups_for_user'):
            return HttpResponseForbidden()
            
        # Get all groups of a user
        username = request.GET['user'].lower()
            
        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=username)

        groups = user.get_groups(service)
        names = [ group.name for group in groups ]

        logger.debug('Get groups for user %s'%(username), extra=log_args)
        return HttpRestAuthResponse(request, names) # Ok
    elif request.method == 'GET': # Get a list of groups:
        if not request.user.has_perm('Groups.groups_list'):
            return HttpResponseForbidden()
            
        # get all groups for this service
        groups = Group.objects.filter(service=service)
        groups = list(groups.values_list('name', flat=True))
        
        logger.debug('Get all groups', extra=log_args)
        return HttpRestAuthResponse(request, groups) # Ok
    elif request.method == 'POST': # Create a group
        if not request.user.has_perm('Groups.group_create'):
            return HttpResponseForbidden()
            
        # If BadRequest: 400 Bad Request
        groupname = get_dict(request, [ u'group' ])

        # If ResourceExists: 409 Conflict
        group = group_create(groupname, service)
        
        logger.info('%s: Created group'%(groupname), extra=log_args)
        return HttpResponseCreated(request, group) # Created
    else: # pragma: no cover
        logger.error('%s: Method not allowed: %s'%(service, request.method))
        return HttpResponse(status=405) # method not allowed

@login_required(realm='/groups/<group>/')
#@sql_profile()
def group_handler(request, groupname):
    service = request.user
    logger = logging.getLogger('groups.group')
    log_args = { 'service': service, 'group': groupname }
    
    # If Group.DoesNotExist: 404 Not Found
    group = Group.objects.only('name').get(name=groupname, service=service)
    
    if request.method == 'GET': # Verify that a group exists:
        if not request.user.has_perm('Groups.group_exists'):
            return HttpResponseForbidden()
            
        logger.debug("Check if group exists", extra=log_args)
        return HttpResponseNoContent()
    if request.method == 'DELETE': # Delete group
        if not request.user.has_perm('Groups.group_delete'):
            return HttpResponseForbidden()
            
        group.delete()
        logger.info("Deleted group", extra=log_args)
        return HttpResponseNoContent() # OK
    else: # pragma: no cover
        logger.error('%s: Method not allowed: %s'%(service, request.method))
        return HttpResponse(status=405)

@login_required(realm='/groups/<group>/users/')
#@sql_profile()
def group_users_index_handler(request, groupname):
    service = request.user
    logger = logging.getLogger('groups.group.users')
    log_args = { 'service': service, 'group': groupname }
    
    # If Group.DoesNotExist: 404 Not Found
    group = Group.objects.only('name').get(name=groupname, service=service)

    if request.method == 'GET': # Get all users in a group
        if not request.user.has_perm('Groups.group_users'):
            return HttpResponseForbidden()
            
        users = group.get_members()
        
        # If MarshalError: 500 Internal Server Error
        logger.debug("Get users in group", extra=log_args)
        return HttpRestAuthResponse(request, list(users))
    elif request.method == 'POST': # Add a user to a group
        if not request.user.has_perm('Groups.group_add_user'):
            return HttpResponseForbidden()
            
        # If BadRequest: 400 Bad Request
        username = get_dict(request, [ u'user' ])
        
        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('username').get(username=username)
                         
        group.users.add(user)

        logger.info('Add user "%s"'%(username), extra=log_args)
        return HttpResponseNoContent()
    else: # pragma: no cover
        logger.error('%s: Method not allowed: %s'%(service, request.method))
        return HttpResponse(status=405)

@login_required(realm='/groups/<group>/users/<user>/')
#@sql_profile()
def group_user_handler(request, groupname, username):
    service = request.user
    username = username.lower()
    logger = logging.getLogger('groups.group.users.user')
    log_args = { 'service': service, 'group': groupname, 'user': username }
    
    # If Group.DoesNotExist: 404 Not Found
    group = Group.objects.only('name').get(name=groupname, service=service)
    # If User.DoesNotExist: 404 Not Found
    user = ServiceUser.objects.only('username').get(username=username)
    
    if request.method == 'GET': # Verify that a user is in a group
        if not request.user.has_perm('Groups.group_user_in_group'):
            return HttpResponseForbidden()
            
        logger.debug('Check if user is in group', extra=log_args)
        if group.is_member(user):
            return HttpResponseNoContent()
        else:
            raise ServiceUser.DoesNotExist() # 404 Not Found
    elif request.method == 'DELETE': # Remove user from a group
        if not request.user.has_perm('Groups.group_remove_user'):
            return HttpResponseForbidden()
            
        if not group.is_member(user, False):
            raise User.DoesNotExist() # 404 Not Found

        group.users.remove(user)
        logger.info('Remove user from group', extra=log_args)
        return HttpResponseNoContent()
    else: # pragma: no cover
        logger.error('%s: Method not allowed: %s'%(service, request.method))
        return HttpResponse(status=405)

@login_required(realm='/groups/<group>/groups/')
#@sql_profile()
def group_groups_index_handler(request, groupname):
    service = request.user
    logger = logging.getLogger('groups.group.groups')
    log_args = { 'service': service, 'group': groupname }
    
    # If Group.DoesNotExist: 404 Not Found
    group = Group.objects.only('name').get(name=groupname, service=service)
    if request.method == 'GET': # get a list of sub-groups
        if not request.user.has_perm('Groups.group_groups_list'):
            return HttpResponseForbidden()
            
        groups = group.groups.filter(service=service).values_list('name', flat=True)

        # If MarshalError: 500 Internal Server Error
        logger.debug('Get subgroups', extra=log_args)
        return HttpRestAuthResponse(request, list(groups))
    elif request.method == 'POST': # Add a sub-group:
        if not request.user.has_perm('Groups.group_add_group'):
            return HttpResponseForbidden()
            
        # If BadRequest: 400 Bad Request
        sub_groupname = get_dict(request, [ u'group' ])
        
        # If Group.DoesNotExist: 404 Not Found
        sub_group = Group.objects.only('name').get(name=sub_groupname, service=service)
        
        group.groups.add(sub_group)
        logger.info('Add subgroup "%s"', sub_groupname, extra=log_args)
        return HttpResponseNoContent()
    else: # pragma: no cover
        logger.error('%s: Method not allowed: %s'%(service, request.method))
        return HttpResponse(status=405)

@login_required(realm='/groups/<meta-group>/groups/<sub-group>/')
#@sql_profile()
def group_groups_handler(request, meta_groupname, sub_groupname):
    service = request.user
    logger = logging.getLogger('groups.group.groups.subgroup')
    log_args = { 'service': service, 'group': meta_groupname, 'subgroup': sub_groupname }
    
    # If Group.DoesNotExist: 404 Not Found
    meta_group = Group.objects.only('name').get(name=meta_groupname, service=service)
    # If Group.DoesNotExist: 404 Not Found
    sub_group = Group.objects.only('name').get(name=sub_groupname, service=service)

    if request.method == 'DELETE': # Remove group from a group
        if not request.user.has_perm('Groups.group_remove_group'):
            return HttpResponseForbidden()
            
        if not meta_group.groups.filter(name=sub_groupname, service=service).exists():
            raise Group.DoesNotExist()

        meta_group.groups.remove(sub_group)
        logger.info('Remove subgroup %s', sub_groupname, extra=log_args)
        return HttpResponseNoContent()
    else: # pragma: no cover
        logger.error('%s: Method not allowed: %s'%(service, request.method))
        return HttpResponse(status=405)
