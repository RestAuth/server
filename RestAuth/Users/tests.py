"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.conf import settings

from RestAuth.common import errors
from RestAuth.common.testdata import *

from Users import views
from Users.models import ServiceUser, user_create, Property

class UsersIndexTests( RestAuthTest ):
        
    def test_get_empty_users( self ):
        request = self.get( '/users/' )
        
        response = views.index( request )
        self.assertEquals( response.status_code, httplib.OK )
        body = response.content.decode( 'utf-8' )
        self.assertItemsEqual( self.content_handler.unmarshal_list(body), [] )
        
    def test_get_one_user( self ):
        user_create( username1, 'blahugo' )
        
        request = self.get( '/users/' )
        resp = views.index( request )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertItemsEqual( self.parse( resp, 'list' ), [username1] )
    
    def test_get_two_users( self ):
        user_create( username1, 'blahugo' )
        user_create( username2, 'blahugo' )
        
        request = self.get( '/users/' )
        resp = views.index( request )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertItemsEqual( self.parse( resp, 'list' ),
                              [username1, username2] )
        
    def test_add_user( self ):
        request = self.post( '/users/', { 'user': username1, 'password': 'foobar' } )
        
        resp = views.index( request )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        self.assertEquals( self.get_usernames(), [username1] )
    
    def test_add_two_users( self ):
        request = self.post( '/users/', { 'user': username1, 'password': 'foobar' } )
        resp = views.index( request )
        self.assertEquals( resp.status_code, httplib.CREATED )
        request = self.post( '/users/', { 'user': username2, 'password': 'foobar' } )
        resp = views.index( request )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        self.assertEquals( self.get_usernames(), [username1, username2] )
        
    def test_add_user_twice( self ):
        self.assertEquals( self.get_usernames(), [] )
        request = self.post( '/users/', { 'user': username1, 'password': 'foobar' } )
        resp = self.make_request( views.index, request )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( self.get_usernames(), [username1] )
        request = self.post( '/users/', { 'user': username1, 'password': 'foobar' } )
        resp = self.make_request( views.index, request )
        self.assertEquals( resp.status_code, httplib.CONFLICT )
        self.assertEquals( self.get_usernames(), [username1] )
        
    def test_make_wrong_request( self ):
        self.assertEquals( self.get_usernames(), [] )
        
        request = self.post( '/users/', { 'user': username1 } )
        resp = self.make_request( views.index, request )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( self.get_usernames(), [] )
        
        request = self.post( '/users/', { 'password': 'foobar' } )
        resp = self.make_request( views.index, request )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( self.get_usernames(), [] )
        
        request = self.post( '/users/', {} )
        resp = self.make_request( views.index, request )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( self.get_usernames(), [] )
        
        request = self.post( '/users/', { 'userasdf': username1, 'passwordasdf': 'foobar' } )
        resp = self.make_request( views.index, request )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( self.get_usernames(), [] )
    
class UsersUserTests( RestAuthTest ):
    def test_user_exists( self ):
        request = self.get( '/users/%s'%username1 )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        user_create( username1, 'foobar' )
        
        request = self.get( '/users/%s'%username1 )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
    def test_verify_password( self ):
        # doesn't exist:
        request = self.post( '/users/%s'%username1, { 'password': 'foobar' } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        # create and verify
        user_create( username1, 'foobar' )
        request = self.post( '/users/%s'%username1, { 'password': 'foobar' } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
        # verify wrong password
        request = self.post( '/users/%s'%username1, { 'password': 'wrong' } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        # bad requests:
        request = self.post( '/users/%s'%username1, {} )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        
        # bad requests:
        request = self.post( '/users/%s'%username1, {'foo': 'bar'} )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        
        request = self.post( '/users/%s'%username1, {'password': 'foobar', 'foo': 'bar'} )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        
        
    def test_change_password( self ):
        # doesn't exist:
        request = self.put( '/users/%s'%username1, { 'password': password1 } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
    
        user = user_create( username1, password1 )
        self.assertTrue( user.check_password( password1 ) )
        
        # works:
        request = self.put( '/users/%s'%username1, { 'password': password1 } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertTrue( ServiceUser.objects.get( username=username1 ).check_password( password1 ) )
        self.assertFalse( ServiceUser.objects.get( username=username1 ).check_password( password2 ) )
        
        # update password
        request = self.put( '/users/%s'%username1, { 'password': password2 } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
        # check new and old password:
        self.assertFalse( ServiceUser.objects.get( username=username1 ).check_password( password1 ) )
        self.assertTrue( ServiceUser.objects.get( username=username1 ).check_password( password2 ) )
        
        # some bad requests:
        request = self.put( '/users/%s'%username1, { 'foo': password2 } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertFalse( ServiceUser.objects.get( username=username1 ).check_password( password1 ) )
        self.assertTrue( ServiceUser.objects.get( username=username1 ).check_password( password2 ) )
        
        request = self.put( '/users/%s'%username1, {} )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertFalse( ServiceUser.objects.get( username=username1 ).check_password( password1 ) )
        self.assertTrue( ServiceUser.objects.get( username=username1 ).check_password( password2 ) )
        
        request = self.put( '/users/%s'%username1, { 'password': password3, 'foo': 'bar' } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertFalse( ServiceUser.objects.get( username=username1 ).check_password( password1 ) )
        self.assertTrue( ServiceUser.objects.get( username=username1 ).check_password( password2 ) )
    
    def test_delete_user( self ):
        # doesn't exist:
        request = self.delete( '/users/%s'%username1 )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
    
        user_create( username1, password1 )
        self.assertTrue( ServiceUser.objects.filter( username=username1 ).exists() )
        
        # delete user
        request = self.delete( '/users/%s'%username1 )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertFalse( ServiceUser.objects.filter( username=username1 ).exists() )
        
class UsersUserPropsTests( RestAuthTest ):
    def test_user_doesnot_exist( self ):
        request = self.get( '/users/%s'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        request = self.post( '/users/%s'%username1, {} )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        request = self.put( '/users/%s'%username1, {} )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        request = self.delete( '/users/%s'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_get_all_properties( self ):
        # two users, so we can make sure nothing leaks to the other user
        user1 = user_create( username1, password1 )
        user2 = user_create( username2, password2 )
        
        request = self.get( '/users/%s/props/'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
        request = self.get( '/users/%s/props/'%username2 )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
        user1.add_property( propkey1, propval1 )
        
        request = self.get( '/users/%s/props/'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey1: propval1} )
        
        request = self.get( '/users/%s/props/'%username2 )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
        user1.add_property( propkey2, propval2 )
        
        request = self.get( '/users/%s/props/'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey1: propval1, propkey2: propval2} )
        
        request = self.get( '/users/%s/props/'%username2 )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
        user2.add_property( propkey3, propval3 )
        
        request = self.get( '/users/%s/props/'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey1: propval1, propkey2: propval2} )
        
        request = self.get( '/users/%s/props/'%username2 )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey3: propval3} )
        
    def test_create_property( self ):
        # two users, so we can make sure nothing leaks to the other user
        user1 = user_create( username1, password1 )
        user2 = user_create( username2, password2 )
        self.assertDictEqual( user1.get_properties(), {} )
        self.assertDictEqual( user2.get_properties(), {} )
        
        request = self.post( '/users/%s/props/'%username1, {'prop': propkey1, 'value': propval1} )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        self.assertDictEqual( user1.get_properties(), {propkey1: propval1} )
        self.assertDictEqual( user2.get_properties(), {} )
        
        request = self.post( '/users/%s/props/'%username1, {'prop': propkey1, 'value': propval2} )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.CONFLICT )
        
        self.assertDictEqual( user1.get_properties(), {propkey1: propval1} )
        self.assertDictEqual( user2.get_properties(), {} )
        
        request = self.post( '/users/%s/props/'%username1, {'prop': propkey2, 'value': propval2} )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        self.assertDictEqual( user1.get_properties(), {propkey1: propval1, propkey2: propval2} )
        self.assertDictEqual( user2.get_properties(), {} )
        
        request = self.post( '/users/%s/props/'%username2, {'prop': propkey3, 'value': propval3} )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        self.assertDictEqual( user1.get_properties(), {propkey1: propval1, propkey2: propval2} )
        self.assertDictEqual( user2.get_properties(), {propkey3: propval3} )
        
        # try a few bad requests:
        request = self.post( '/users/%s/props/'%username2, {} )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertDictEqual( user1.get_properties(), {propkey1: propval1, propkey2: propval2} )
        self.assertDictEqual( user2.get_properties(), {propkey3: propval3} )
        
        request = self.post( '/users/%s/props/'%username2, {'foo': 'bar'} )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertDictEqual( user1.get_properties(), {propkey1: propval1, propkey2: propval2} )
        self.assertDictEqual( user2.get_properties(), {propkey3: propval3} )
        
        request = self.post( '/users/%s/props/'%username2, {'foo': 'bar', 'prop': propkey3, 'value': propval3} )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertDictEqual( user1.get_properties(), {propkey1: propval1, propkey2: propval2} )
        self.assertDictEqual( user2.get_properties(), {propkey3: propval3} )
        
        
        
__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}

