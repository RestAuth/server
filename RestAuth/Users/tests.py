"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.conf import settings

from RestAuth.common import errors
from RestAuth.common.testdata import *

from Users import views
from Users.models import ServiceUser, user_create, Property, user_get

class GetUsersTests( RestAuthTest ): # GET /users/
    def test_get_empty_users( self ):
        request = self.get( '/users/' )
        
        response = views.index( request )
        self.assertEquals( response.status_code, httplib.OK )
        body = response.content.decode( 'utf-8' )
        self.assertItemsEqual( self.content_handler.unmarshal_list(body), [] )
        
    def test_get_one_user( self ):
        user_create( username1, password1 )
        
        request = self.get( '/users/' )
        resp = views.index( request )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertItemsEqual( self.parse( resp, 'list' ), [username1] )
        
    def test_get_two_users( self ):
        user_create( username1, password1 )
        user_create( username2, password1 )
        
        request = self.get( '/users/' )
        resp = views.index( request )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertItemsEqual( self.parse( resp, 'list' ),
                              [username1, username2] )

class AddUserTests( RestAuthTest ): # POST /users/
    def get_usernames( self ):
        return list( ServiceUser.objects.values_list( 'username', flat=True ) )
    
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
        
        # add again:
        request = self.post( '/users/', { 'user': username1, 'password': 'foobar' } )
        resp = self.make_request( views.index, request )
        self.assertEquals( resp.status_code, httplib.CONFLICT )
        self.assertEquals( self.get_usernames(), [username1] )
        
    def test_bad_requests( self ):
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
    
class UserTests( RestAuthTest ):
    def setUp( self ):
        RestAuthTest.setUp( self )
        
        # two users, so we can make sure nothing leaks to the other user
        self.user1 = user_create( username1, password1 )
        self.user2 = user_create( username2, password2 )
        
    def tearDown( self ):
        RestAuthTest.tearDown( self )
        ServiceUser.objects.all().delete()
        
class UserExistsTests( UserTests ): # GET /users/<user>/
    def test_user_exists( self ):
        request = self.get( '/users/%s/'%username1 )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
        request = self.get( '/users/%s/'%username2 )
        resp = self.make_request( views.user_handler, request, username2 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
        request = self.get( '/users/%s/'%username3 )
        resp = self.make_request( views.user_handler, request, username3 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
    
class VerifyPasswordsTest( UserTests ): # POST /users/<user>/
    def test_user_doesnt_exist( self ):
        request = self.post( '/users/%s'%username3, { 'password': 'foobar' } )
        resp = self.make_request( views.user_handler, request, username3 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_verify_password( self ):
        request = self.post( '/users/%s'%username1, { 'password': password1 } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
        request = self.post( '/users/%s'%username2, { 'password': password2 } )
        resp = self.make_request( views.user_handler, request, username2 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
    def test_verify_wrong_password( self ):
        request = self.post( '/users/%s'%username1, { 'password': 'wrong' } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        request = self.post( '/users/%s'%username2, { 'password': 'wrong' } )
        resp = self.make_request( views.user_handler, request, username2 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_bad_requests( self ):
        request = self.post( '/users/%s'%username1, {} )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        
        request = self.post( '/users/%s'%username1, {'foo': 'bar'} )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        
        request = self.post( '/users/%s'%username1, {'password': 'foobar', 'foo': 'bar'} )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
    
class ChangePasswordsTest( UserTests ): # PUT /users/<user>/
    def test_user_doesnt_exist( self ):
        request = self.put( '/users/%s/'%username3, { 'password': password3 } )
        resp = self.make_request( views.user_handler, request, username3 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEquals( resp['Resource-Type'], 'user' )
    
    def test_change_password( self ):
        request = self.put( '/users/%s'%username1, { 'password': password3 } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertFalse( user_get( username1 ).check_password( password1 ) )
        self.assertFalse( user_get( username1 ).check_password( password2 ) )
        self.assertTrue( user_get( username1 ).check_password( password3 ) )
        
        # check user2, just to be sure:
        self.assertFalse( user_get( username2 ).check_password( password1 ) )
        self.assertTrue( user_get( username2 ).check_password( password2 ) )
        self.assertFalse( user_get( username2 ).check_password( password3 ) )
    
    def test_bad_requests( self ):            
        request = self.put( '/users/%s'%username1, { 'foo': password2 } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
        
        request = self.put( '/users/%s'%username1, {} )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
        
        request = self.put( '/users/%s'%username1, { 'password': password3, 'foo': 'bar' } )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
    
class DeleteUserTest( UserTests ): # DELETE /users/<user>/
    def test_user_doesnt_exist( self ):
        request = self.delete( '/users/%s/'%username3 )
        resp = self.make_request( views.user_handler, request, username3 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
    
    def test_delete_user( self ):
        request = self.delete( '/users/%s'%username1 )
        resp = self.make_request( views.user_handler, request, username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertFalse( ServiceUser.objects.filter( username=username1 ).exists() )
        self.assertTrue( ServiceUser.objects.filter( username=username2 ).exists() )
        
class PropertyTests( RestAuthTest ):
    """
    Superclass for tests on /users/<user>/props/ and /users/<user>/props/<prop>/.
    """
    def setUp( self ):
        RestAuthTest.setUp( self )
        
        # two users, so we can make sure nothing leaks to the other user
        self.user1 = user_create( username1, password1 )
        self.user2 = user_create( username2, password2 )
        
    def tearDown( self ):
        RestAuthTest.tearDown( self )
        ServiceUser.objects.all().delete()
        
class GetAllPropertiesTests( PropertyTests ): # GET /users/<user>/props/
    def test_user_doesnot_exist( self ):
        request = self.get( '/users/%s/props/'%username3 )
        resp = self.make_request( views.userprops_index, request, username3 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_get_no_properties( self ):
        request = self.get( '/users/%s/props/'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
        request = self.get( '/users/%s/props/'%username2 )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
    def test_get_single_property( self ):
        self.user1.add_property( propkey1, propval1 )
        
        request = self.get( '/users/%s/props/'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey1: propval1} )
        
        request = self.get( '/users/%s/props/'%username2 )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
    def test_get_two_properties( self ):
        self.user1.add_property( propkey1, propval1 )
        self.user1.add_property( propkey2, propval2 )
        
        request = self.get( '/users/%s/props/'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey1: propval1, propkey2: propval2} )
        
        request = self.get( '/users/%s/props/'%username2 )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
    def test_get_multiple_properties( self ):
        self.user1.add_property( propkey1, propval1 )
        self.user1.add_property( propkey2, propval2 )
        self.user2.add_property( propkey3, propval3 )
        
        request = self.get( '/users/%s/props/'%username1 )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey1: propval1, propkey2: propval2} )
        
        request = self.get( '/users/%s/props/'%username2 )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey3: propval3} )
        
class CreatePropertyTests( PropertyTests ): # POST /users/<user>/props/
    def test_user_doesnt_exist( self ):
        request = self.post( '/users/%s/props/'%username3, { 'prop': propkey1, 'value': propval1 } )
        resp = self.make_request( views.userprops_index, request, username3 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        # check that no properties were added to the database:
        self.assertEquals( list( Property.objects.all()), [] )
        
    def test_create_property( self ):
        request = self.post( '/users/%s/props/'%username1, {'prop': propkey1, 'value': propval1} )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        self.assertDictEqual( self.user1.get_properties(), {propkey1: propval1} )
        self.assertDictEqual( self.user2.get_properties(), {} )
        
        # we create a second property
        request = self.post( '/users/%s/props/'%username1, {'prop': propkey2, 'value': propval2} )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        self.assertDictEqual( self.user1.get_properties(), {propkey1: propval1, propkey2: propval2} )
        self.assertDictEqual( self.user2.get_properties(), {} )
        
        # and a property for second user:
        request = self.post( '/users/%s/props/'%username2, {'prop': propkey3, 'value': propval3} )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertDictEqual( self.user1.get_properties(), {propkey1: propval1, propkey2: propval2} )
        self.assertDictEqual( self.user2.get_properties(), {propkey3: propval3} )
        
    def test_create_existing_property( self ):
        self.user1.add_property( propkey1, propval1 )
        
        request = self.post( '/users/%s/props/'%username1, {'prop': propkey1, 'value': propval2} )
        resp = self.make_request( views.userprops_index, request, username1 )
        self.assertEquals( resp.status_code, httplib.CONFLICT )
        
        self.assertDictEqual( self.user1.get_properties(), {propkey1: propval1} )
        self.assertDictEqual( self.user2.get_properties(), {} )   

    def test_bad_requests( self ):
        request = self.post( '/users/%s/props/'%username2, {} )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertDictEqual( self.user1.get_properties(), {} )
        self.assertDictEqual( self.user2.get_properties(), {} )
        
        request = self.post( '/users/%s/props/'%username2, {'foo': 'bar'} )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertDictEqual( self.user1.get_properties(), {} )
        self.assertDictEqual( self.user2.get_properties(), {} )
        
        request = self.post( '/users/%s/props/'%username2, {'foo': 'bar', 'prop': propkey3,
                                                            'value': propval3} )
        resp = self.make_request( views.userprops_index, request, username2 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertDictEqual( self.user1.get_properties(), {} )
        self.assertDictEqual( self.user2.get_properties(), {} )

class GetPropertyTests( PropertyTests ): # GET /users/<user>/props/<prop>/
    def test_user_doesnt_exist( self ):
        request = self.get( '/users/%s/props/%s/'%(username3, propkey1) )
        resp = self.make_request( views.userprops_prop, request, username3, propkey1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_property_doesnt_exist( self ):
        request = self.get( '/users/%s/props/%s/'%(username1, propkey1) )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'property' )
        
    def test_get_property( self ):
        self.user1.add_property( propkey1, propval1 )
        
        request = self.get( '/users/%s/props/%s/'%(username1, propkey1) )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertEquals( self.parse( resp, 'str' ), propval1 ) # return old value
        
        # check that user2 doesn't have it:
        request = self.get( '/users/%s/props/%s/'%(username2, propkey1) )
        resp = self.make_request( views.userprops_prop, request, username2, propkey1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'property' )
      
class SetPropertyTests( PropertyTests ): # PUT /users/<user>/props/<prop>/
    def test_user_doesnt_exist( self ):
        request = self.put( '/users/%s/props/%s/'%(username3, propkey1), {'value': propval1} )
        resp = self.make_request( views.userprops_prop, request, username3, propkey1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        # assert that no property has been created:
        self.assertEquals( list( Property.objects.all()), [] )
        
    def test_set_new_property( self ):
        # set a property
        request = self.put( '/users/%s/props/%s/'%(username1, propkey1), {'value': propval1} )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( user_get( username1 ).property_set.get( key=propkey1 ).value, propval1 )
        self.assertFalse( user_get( username2 ).property_set.filter( key=propkey1 ).exists() )
        
    def test_set_existing_property( self ):
        self.user1.add_property( propkey1, propval1 )
        
        # set a property again and assert that it returns the old value:
        request = self.put( '/users/%s/props/%s/'%(username1, propkey1), {'value': propval2} )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertEquals( self.parse( resp, 'str' ), propval1 ) # old value returned
        self.assertEquals( user_get( username1 ).property_set.get( key=propkey1 ).value, propval2 )
        self.assertFalse( user_get( username2 ).property_set.filter( key=propkey1 ).exists() )
        
    def test_bad_request( self ):
        # do some bad request tests:
        request = self.put( '/users/%s/props/%s/'%(username1, propkey1), {} )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( list( Property.objects.all().values_list( 'key', 'value' )) , [] )
        
        request = self.put( '/users/%s/props/%s/'%(username1, propkey1), {'foo': 'bar'} )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( list( Property.objects.all().values_list( 'key', 'value' )), [] )
        
        request = self.put( '/users/%s/props/%s/'%(username1, propkey1), {'value': propkey3, 'foo':'bar'} )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( list( Property.objects.all().values_list( 'key', 'value' )), [] )
        
class DeletePropertyTests( PropertyTests ): # DELETE /users/<user>/props/<prop>/
    def test_user_doesnt_exist( self ):
        request = self.delete( '/users/%s/props/%s/'%(username3, propkey1), )
        resp = self.make_request( views.userprops_prop, request, username3, propkey1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_property_doesnt_exist( self ):
        request = self.delete( '/users/%s/props/%s/'%(username1, propkey1), )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'property' )
        
    def test_delete_property( self ):
        self.user1.add_property( propkey1, propval1 )
        self.user1.add_property( propkey2, propval2 )
        
        request = self.delete( '/users/%s/props/%s/'%(username1, propkey1), )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertItemsEqual( self.user1.property_set.values_list( 'key', 'value' ).all(),
                          [(propkey2, propval2)] )
        
    def test_cross_user( self ):
        # two users have properties with the same key, we verify that deleting one doesn't delete
        # the other:
        self.user1.add_property( propkey1, propval1 )
        self.user2.add_property( propkey1, propval1 )
        
        request = self.delete( '/users/%s/props/%s/'%(username1, propkey1), )
        resp = self.make_request( views.userprops_prop, request, username1, propkey1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertItemsEqual( list( self.user1.property_set.all() ), [] )
        self.assertItemsEqual( self.user2.property_set.values_list( 'key', 'value' ).all(),
                          [(propkey1, propval1)] )
        
    
__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}

