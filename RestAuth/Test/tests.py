"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from RestAuth.Users.models import ServiceUser
from RestAuth.Groups.models import Group
from RestAuth.Services.models import Service
from RestAuth.common.testdata import *
from RestAuthCommon.handlers import json

from django.db import transaction
from django.contrib.auth.models import User

from django.test.client import Client
from django.utils import unittest

class CreateUserTest( unittest.TestCase ):
    def setUp( self ):
        self.c = Client()
        self.handler = json()
        self.extra = {
            'HTTP_ACCEPT': json.mime,
            'REMOTE_USER': 'vowi',
            'content_type': json.mime,
        }
        
    def tearDown( self ):
        ServiceUser.objects.all().delete()
        
    def test_dry_run_create_user( self ):
        content = self.handler.marshal_dict({'user':username1})
        resp = self.c.post( '/test/users/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CREATED )
        self.assertFalse( ServiceUser.objects.all() )
        
    def test_dry_run_create_user_with_pass( self ):
        content = self.handler.marshal_dict({'user':username1, 'password': password1})
        resp = self.c.post( '/test/users/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CREATED )
        self.assertFalse( ServiceUser.objects.all() )
        
    def test_dry_run_create_user_with_props( self ):
        content = self.handler.marshal_dict({'user':username1, 'properties': {'foo': 'bar'}})
        resp = self.c.post( '/test/users/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CREATED )
        self.assertFalse( ServiceUser.objects.all() )
        
    def test_dry_run_create_user_with_pass_and_props( self ):
        content = self.handler.marshal_dict({
            'user': username1,
            'password': password1,
            'properties': {'foo': 'bar'}
        })
        resp = self.c.post( '/test/users/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CREATED )
        self.assertFalse( ServiceUser.objects.all() )
    
    def test_dry_run_create_existing_user( self ):
        user = ServiceUser.objects.create( username=username1 )
        user.save()
        
        content = self.handler.marshal_dict({'user':username1})
        resp = self.c.post( '/test/users/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CONFLICT )
        self.assertItemsEqual( [user], ServiceUser.objects.all() )
    
    def test_dry_run_create_invalid_user( self ):
        content = self.handler.marshal_dict({'user':'foo/bar'})
        resp = self.c.post( '/test/users/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.PRECONDITION_FAILED )
        self.assertFalse( ServiceUser.objects.all() )
    
    def test_dry_run_create_short_user( self ):
        content = self.handler.marshal_dict({'user':'x'})
        resp = self.c.post( '/test/users/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.PRECONDITION_FAILED )
        self.assertFalse( ServiceUser.objects.all() )
        
    def test_create_with_too_short_pass( self ):
        content = self.handler.marshal_dict({'user': username1, 'password': 'a'})
        resp = self.c.post( '/test/users/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.PRECONDITION_FAILED )
        self.assertFalse( ServiceUser.objects.all() )
    
class CreatePropertyTest( unittest.TestCase ):
    def setUp( self ):
        self.c = Client()
        self.handler = json()
        self.extra = {
            'HTTP_ACCEPT': json.mime,
            'REMOTE_USER': 'vowi',
            'content_type': json.mime,
        }
        
        self.user = ServiceUser.objects.create( username=username1 )
        self.user.save()
        
    def tearDown(self):
        ServiceUser.objects.all().delete()
        
    def test_create_property( self ):
        url = '/test/users/%s/props/'%self.user.username
        content = self.handler.marshal_dict({'prop': propkey1, 'value': propval1})
        resp = self.c.post( url, content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CREATED )
        
        self.assertFalse( self.user.property_set.all() )
    
    def test_create_existing_property( self ):
        prop = self.user.add_property( propkey1, propval1 )
        
        url = '/test/users/%s/props/'%self.user.username
        content = self.handler.marshal_dict({'prop': propkey1, 'value': propval2})
        resp = self.c.post( url, content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CONFLICT )
        
        self.assertEqual( prop, self.user.property_set.get( key=propkey1 ) )
    
    def test_create_invalid_property( self ):
        url = '/test/users/%s/props/'%self.user.username
        content = self.handler.marshal_dict({'prop': propkey1, 'value': 'foo/bar'})
        resp = self.c.post( url, content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CREATED )
        
        self.assertFalse( self.user.property_set.all() )
    
    def test_create_property_for_non_existing_user( self ):
        url = '/test/users/%s/props/'%'wronguser'
        content = self.handler.marshal_dict({'prop': propkey1, 'value': propval1})
        resp = self.c.post( url, content, **self.extra )
        self.assertEqual( resp.status_code, httplib.NOT_FOUND )
        
        self.assertFalse( self.user.property_set.all() )
    
    def test_create_property_for_invalid_user( self ):
        url = '/test/users/%s/props/'%'wrong\user'
        content = self.handler.marshal_dict({'prop': propkey1, 'value': propval1})
        resp = self.c.post( url, content, **self.extra )
        self.assertEqual( resp.status_code, httplib.NOT_FOUND )
        
        self.assertFalse( self.user.property_set.all() )
    

class CreateGroupTest( unittest.TestCase ):
    def setUp( self ):
        self.c = Client()
        self.handler = json()
        self.extra = {
            'HTTP_ACCEPT': json.mime,
            'REMOTE_USER': 'vowi',
            'content_type': json.mime,
        }
        self.service = Service.objects.get_or_create( username='vowi' )[0]
        self.service.save()
        
    def tearDown(self):
        Group.objects.all().delete()
        
    def test_dry_run_create_group( self ):
        content = self.handler.marshal_dict({'group': groupname1})
        resp = self.c.post( '/test/groups/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CREATED )
        self.assertFalse( Group.objects.all() )
    
    def test_dry_run_create_existing_group( self ):
        group = Group( name=groupname1, service=self.service )
        group.save()
        
        content = self.handler.marshal_dict({'group': groupname1})
        resp = self.c.post( '/test/groups/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.CONFLICT )
        self.assertItemsEqual( [group], Group.objects.all() )
    
    def test_dry_run_create_invalid_group( self ):
        content = self.handler.marshal_dict({'group': 'foo/bar'})
        resp = self.c.post( '/test/groups/', content, **self.extra )
        self.assertEqual( resp.status_code, httplib.PRECONDITION_FAILED )
        self.assertFalse( Group.objects.all() )