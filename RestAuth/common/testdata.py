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

import base64, httplib, logging

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TransactionTestCase
from django.test.client import Client
from django.conf import settings

import RestAuthCommon

from RestAuth.Services.models import Service, service_create
from RestAuth.Users.models import ServiceUser, user_create
from RestAuth.common.middleware import ExceptionMiddleware

username1 = u"mati \u6111"
username2 = u"mati \u6112"
username3 = u"mati \u6113"
username4 = u"mati \u6114"
username5 = u"mati \u6115"

password1 = u"password \u6121"
password2 = u"password \u6122"
password3 = u"password \u6123"
password4 = u"password \u6124"
password5 = u"password \u6125"

groupname1 = u"group 1 \u6131"
groupname2 = u"group 2 \u6132"
groupname3 = u"group 3 \u6133"
groupname4 = u"group 4 \u6134"
groupname5 = u"group 5 \u6135"
groupname6 = u"group 6 \u6136"
groupname7 = u"group 7 \u6137"
groupname8 = u"group 8 \u6138"
groupname9 = u"group 9 \u6139"

propkey1 = u"propkey \u6141"
propkey2 = u"propkey \u6142"
propkey3 = u"propkey \u6143"
propkey4 = u"propkey \u6144"
propkey5 = u"propkey \u6145"

propval1 = u"propval \u6151"
propval2 = u"propval \u6152"
propval3 = u"propval \u6153"
propval4 = u"propval \u6154"
propval5 = u"propval \u6155"


class RestAuthTest( TransactionTestCase ):
    def setUp(self):
        if hasattr( self, 'settings' ): # requires django-1.4:
            self.settings( LOGGING_CONFIG=None )
        
        self.c = Client()
        self.handler = RestAuthCommon.handlers.json()
        self.extra = {
            'HTTP_ACCEPT': self.handler.mime,
            'REMOTE_USER': 'vowi',
            'content_type': self.handler.mime,
        }
        self.service = service_create( 'vowi', 'vowi', [ '127.0.0.1', '::1' ] )
        
        # add permissions:
        u_ct = ContentType.objects.get(app_label="Users", model="serviceuser")
        p_ct = ContentType.objects.get(app_label="Users", model="property")
        g_ct = ContentType.objects.get(app_label="Groups", model="group")
        
        # add user-permissions:
        for codename, name in (
                ('users_list', 'List all users'),
                ('user_create', 'Create a new user'),
                ('user_exists', 'Check if a user exists'),
                ('user_delete', 'Delete a user'),
                ('user_verify_password', 'Verify a users password'),
                ('user_change_password', 'Change a users password'),
                ('user_delete_password', 'Delete a user'),):
            p, c = Permission.objects.get_or_create(codename=codename, content_type=u_ct,
                                                    defaults={'name': name})
            self.service.user_permissions.add(p)
            
        for codename, name in (
                ('props_list', 'List all properties of a user'),
                ('prop_create', 'Create a new property'),
                ('prop_get', 'Get value of a property'),
                ('prop_set', 'Set or create a property'),
                ('prop_delete', 'Delete a property'),):
            p, c = Permission.objects.get_or_create(codename=codename, content_type=p_ct,
                                                    defaults={'name': name})
            self.service.user_permissions.add(p)
            
        for codename, name in (
                ('groups_for_user', 'List groups for a user'),
                ('groups_list', 'List all groups'),
                ('group_create', 'Create a new group'),
                ('group_exists', 'Verify that a group exists'),
                ('group_delete', 'Delete a group'),
                ('group_users', 'List users in a group'),
                ('group_add_user', 'Add a user to a group'),
                ('group_user_in_group', 'Verify that a user is in a group'),
                ('group_remove_user', 'Remove a user from a group'),
                ('group_groups_list', 'List subgroups of a group'),
                ('group_add_group', 'Add a subgroup to a group'),
                ('group_remove_group', 'Remove a subgroup from a group'),):
            
            p, c = Permission.objects.get_or_create(codename=codename, content_type=g_ct,
                                                    defaults={'name': name})
            self.service.user_permissions.add(p)
        
   
    def get( self, url, data={} ):
        return self.c.get( url, data, **self.extra)
    
    def post( self, url, data ):
        post_data = self.handler.marshal_dict( data )
        return self.c.post( url, post_data, **self.extra )
    
    def put( self, url, data ):
        data = self.handler.marshal_dict( data )
        return self.c.put( url, data, **self.extra )
    
    def delete( self, url ):
        return self.c.delete( url, **self.extra )
    
    def parse( self, response, typ ):
        body = response.content.decode( 'utf-8' )
        func = getattr( self.handler, 'unmarshal_%s'%typ )
        return func( body )