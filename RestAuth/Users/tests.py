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

from RestAuth.common import errors
from RestAuth.common.testdata import *

from Users import views
from Users.models import ServiceUser, user_create, Property, user_get

class GetUsersTests( RestAuthTest ): # GET /users/
    def test_get_empty_users( self ):
        resp = self.get( '/users/' )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertItemsEqual( self.parse(resp, 'list'), [] )
        
    def test_get_one_user( self ):
        user_create( username1, password1 )
        
        resp = self.get( '/users/' )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertItemsEqual( self.parse( resp, 'list' ), [username1] )
        
    def test_get_two_users( self ):
        user_create( username1, password1 )
        user_create( username2, password1 )
        
        resp = self.get( '/users/' )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertItemsEqual( self.parse( resp, 'list' ), [username1, username2] )

class AddUserTests( RestAuthTest ): # POST /users/
    def get_usernames( self ):
        return list( ServiceUser.objects.values_list( 'username', flat=True ) )
    
    def test_add_user( self ):
        resp = self.post( '/users/', { 'user': username1, 'password': password1 } )
        
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( self.get_usernames(), [username1] )
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
    
    def test_add_two_users( self ):
        resp = self.post( '/users/', { 'user': username1, 'password': password1 } )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( self.get_usernames(), [username1] )
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
        self.assertFalse( user_get( username1 ).check_password( password2 ) )
        
        resp = self.post( '/users/', { 'user': username2, 'password': password2 } )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( self.get_usernames(), [username1, username2] )
        
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
        self.assertFalse( user_get( username1 ).check_password( password2 ) )
        self.assertTrue( user_get( username2 ).check_password( password2 ) )
        self.assertFalse( user_get( username2 ).check_password( password1 ) )
        
    def test_add_user_twice( self ):
        self.assertEquals( self.get_usernames(), [] )
        resp = self.post( '/users/', { 'user': username1, 'password': password1 } )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( self.get_usernames(), [username1] )
        
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
        self.assertFalse( user_get( username1 ).check_password( password2 ) )
        
        # add again:
        resp = self.post( '/users/', { 'user': username1, 'password': password2 } )
        self.assertEquals( resp.status_code, httplib.CONFLICT )
        self.assertEquals( self.get_usernames(), [username1] )
        
        # check that we still have the old password:
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
        self.assertFalse( user_get( username1 ).check_password( password2 ) )
        
    def test_add_user_no_pass( self ):
        resp = self.post( '/users/', { 'user': username1 } )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( self.get_usernames(), [username1] )
        user = user_get( username1 )
        self.assertFalse( user.check_password( '' ) )
        self.assertFalse( user.check_password( None ) )
        self.assertFalse( user.check_password( password1 ) )
        self.assertFalse( user.check_password( password2 ) )
        
        resp = self.post( '/users/', { 'user': username2, 'password': '' } )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( self.get_usernames(), [username1, username2] )
        user = user_get( username2 )
        self.assertFalse( user.check_password( '' ) )
        self.assertFalse( user.check_password( None ) )
        self.assertFalse( user.check_password( password1 ) )
        self.assertFalse( user.check_password( password2 ) )
        
        resp = self.post( '/users/', { 'user': username3, 'password': None } )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( self.get_usernames(), [username1, username2, username3] )
        user = user_get( username3 )
        self.assertFalse( user.check_password( '' ) )
        self.assertFalse( user.check_password( None ) )
        self.assertFalse( user.check_password( password1 ) )
        self.assertFalse( user.check_password( password2 ) )
        
    def test_add_user_with_property( self ):
        resp = self.post( '/users/', { 'user': username1, 'properties': {propkey1: propval1} } )
        
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( self.get_usernames(), [username1] )
        
        user = user_get( username1 )
        self.assertDictEqual( {propkey1: propval1}, user.get_properties() )
        
    def test_add_user_with_properties( self ):
        props = {propkey1: propval1, propkey2: propval2 }
        resp = self.post( '/users/', { 'user': username1, 'properties': props } )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        user = user_get( username1 )
        self.assertDictEqual( props, user.get_properties() )
        
    def test_bad_requests( self ):
        self.assertEquals( self.get_usernames(), [] )
                
        resp = self.post( '/users/', { 'password': 'foobar' } )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( self.get_usernames(), [] )
        
        resp = self.post( '/users/', {} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( self.get_usernames(), [] )
        
        resp = self.post( '/users/', { 'userasdf': username1, 'passwordasdf': 'foobar' } )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( self.get_usernames(), [] )
        
    def test_add_invalid_username( self ):
        username = 'foo#bar'
        resp = self.post( '/users/', { 'user': username, 'password': password1 } )
        self.assertEquals( resp.status_code, httplib.PRECONDITION_FAILED )
        self.assertEquals( self.get_usernames(), [] )
        
        username = 'foo[bar'
        resp = self.post( '/users/', { 'user': username, 'password': password1 } )
        self.assertEquals( resp.status_code, httplib.PRECONDITION_FAILED )
        self.assertEquals( self.get_usernames(), [] )
        
    def test_add_user_with_long_username( self ):
        username = 'abc'*200
        resp = self.post( '/users/', { 'user': username } )
        self.assertEquals( resp.status_code, httplib.PRECONDITION_FAILED )
        self.assertEquals( self.get_usernames(), [] )
        
    
class UserTests( RestAuthTest ):
    def setUp( self ):
        RestAuthTest.setUp( self )
        
        # two users, so we can make sure nothing leaks to the other user
        self.user1 = user_create( username1, password1 )
        self.user2 = user_create( username2, password2 )
        
class UserExistsTests( UserTests ): # GET /users/<user>/
    def test_user_exists( self ):
        resp = self.get( '/users/%s/'%username1 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
        resp = self.get( '/users/%s/'%username2 )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
        resp = self.get( '/users/%s/'%username3 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
    
class VerifyPasswordsTest( UserTests ): # POST /users/<user>/
    def test_user_doesnt_exist( self ):
        resp = self.post( '/users/%s/'%username3, { 'password': 'foobar' } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_verify_password( self ):
        resp = self.post( '/users/%s/'%username1, { 'password': password1 } )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
        resp = self.post( '/users/%s/'%username2, { 'password': password2 } )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        
    def test_verify_wrong_password( self ):
        resp = self.post( '/users/%s/'%username1, { 'password': 'wrong' } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        resp = self.post( '/users/%s/'%username2, { 'password': 'wrong' } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
    
    def test_verify_disabled_password( self ):
        user3 = user_create( username3, None )
        user4 = user_create( username4, '' )
        
        resp = self.post( '/users/%s/'%username3, { 'password': 'wrong' } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        resp = self.post( '/users/%s/'%username3, { 'password': '' } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        resp = self.post( '/users/%s/'%username3, { 'password': None } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        resp = self.post( '/users/%s/'%username4, { 'password': 'wrong' } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        resp = self.post( '/users/%s/'%username4, { 'password': '' } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        resp = self.post( '/users/%s/'%username4, { 'password': None } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_bad_requests( self ):
        resp = self.post( '/users/%s/'%username1, {} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        
        resp = self.post( '/users/%s/'%username1, {'foo': 'bar'} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        
        resp = self.post( '/users/%s/'%username1, {'password': 'foobar', 'foo': 'bar'} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
    
class ChangePasswordsTest( UserTests ): # PUT /users/<user>/
    def test_user_doesnt_exist( self ):
        resp = self.put( '/users/%s/'%username3, { 'password': password3 } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEquals( resp['Resource-Type'], 'user' )
    
    def test_change_password( self ):
        resp = self.put( '/users/%s/'%username1, { 'password': password3 } )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertFalse( user_get( username1 ).check_password( password1 ) )
        self.assertFalse( user_get( username1 ).check_password( password2 ) )
        self.assertTrue( user_get( username1 ).check_password( password3 ) )
        
        # check user2, just to be sure:
        self.assertFalse( user_get( username2 ).check_password( password1 ) )
        self.assertTrue( user_get( username2 ).check_password( password2 ) )
        self.assertFalse( user_get( username2 ).check_password( password3 ) )
        
    def test_disable_password( self ):
        resp = self.put( '/users/%s/'%username1, {} )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertFalse( user_get( username1 ).check_password( password1 ) )
        self.assertFalse( user_get( username1 ).check_password( '' ) )
        self.assertFalse( user_get( username1 ).check_password( None ) )
        
        resp = self.put( '/users/%s/'%username1, {'password': ''} )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertFalse( user_get( username1 ).check_password( password1 ) )
        self.assertFalse( user_get( username1 ).check_password( '' ) )
        self.assertFalse( user_get( username1 ).check_password( None ) )
        
        resp = self.put( '/users/%s/'%username1, {'password': None} )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertFalse( user_get( username1 ).check_password( password1 ) )
        self.assertFalse( user_get( username1 ).check_password( '' ) )
        self.assertFalse( user_get( username1 ).check_password( None ) )
    
    def test_bad_requests( self ):            
        resp = self.put( '/users/%s/'%username1, { 'foo': password2 } )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
        
        resp = self.put( '/users/%s/'%username1, { 'password': password3, 'foo': 'bar' } )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertTrue( user_get( username1 ).check_password( password1 ) )
    
class DeleteUserTest( UserTests ): # DELETE /users/<user>/
    def test_user_doesnt_exist( self ):
        resp = self.delete( '/users/%s/'%username3 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
    
    def test_delete_user( self ):
        resp = self.delete( '/users/%s/'%username1 )
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
        
class GetAllPropertiesTests( PropertyTests ): # GET /users/<user>/props/
    def test_user_doesnot_exist( self ):
        resp = self.get( '/users/%s/props/'%username3 )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_get_no_properties( self ):
        resp = self.get( '/users/%s/props/'%username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
        resp = self.get( '/users/%s/props/'%username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
    def test_get_single_property( self ):
        self.user1.add_property( propkey1, propval1 )
        
        resp = self.get( '/users/%s/props/'%username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey1: propval1} )
        
        resp = self.get( '/users/%s/props/'%username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
    def test_get_two_properties( self ):
        self.user1.add_property( propkey1, propval1 )
        self.user1.add_property( propkey2, propval2 )
        
        resp = self.get( '/users/%s/props/'%username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey1: propval1, propkey2: propval2} )
        
        resp = self.get( '/users/%s/props/'%username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {} )
        
    def test_get_multiple_properties( self ):
        self.user1.add_property( propkey1, propval1 )
        self.user1.add_property( propkey2, propval2 )
        self.user2.add_property( propkey3, propval3 )
        
        resp = self.get( '/users/%s/props/'%username1 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey1: propval1, propkey2: propval2} )
        
        resp = self.get( '/users/%s/props/'%username2 )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertDictEqual( self.parse( resp, 'dict' ), {propkey3: propval3} )
        
class CreatePropertyTests( PropertyTests ): # POST /users/<user>/props/
    def test_user_doesnt_exist( self ):
        resp = self.post( '/users/%s/props/'%username3, { 'prop': propkey1, 'value': propval1 } )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        # check that no properties were added to the database:
        self.assertEquals( list( Property.objects.all()), [] )
        
    def test_create_property( self ):
        resp = self.post( '/users/%s/props/'%username1, {'prop': propkey1, 'value': propval1} )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        self.assertDictEqual( self.user1.get_properties(), {propkey1: propval1} )
        self.assertDictEqual( self.user2.get_properties(), {} )
        
        # we create a second property
        resp = self.post( '/users/%s/props/'%username1, {'prop': propkey2, 'value': propval2} )
        self.assertEquals( resp.status_code, httplib.CREATED )
        
        self.assertDictEqual( self.user1.get_properties(), {propkey1: propval1, propkey2: propval2} )
        self.assertDictEqual( self.user2.get_properties(), {} )
        
        # and a property for second user:
        resp = self.post( '/users/%s/props/'%username2, {'prop': propkey3, 'value': propval3} )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertDictEqual( self.user1.get_properties(), {propkey1: propval1, propkey2: propval2} )
        self.assertDictEqual( self.user2.get_properties(), {propkey3: propval3} )
        
    def test_create_existing_property( self ):
        self.user1.add_property( propkey1, propval1 )
        
        resp = self.post( '/users/%s/props/'%username1, {'prop': propkey1, 'value': propval2} )
        self.assertEquals( resp.status_code, httplib.CONFLICT )
        
        self.assertDictEqual( self.user1.get_properties(), {propkey1: propval1} )
        self.assertDictEqual( self.user2.get_properties(), {} )
        
    def test_create_invalid_property( self ):
        resp = self.post( '/users/%s/props/'%username1, {'prop': "foo:bar", 'value': propval2} )
        self.assertEquals( resp.status_code, httplib.PRECONDITION_FAILED )
        self.assertDictEqual( self.user1.get_properties(), {} )
        

    def test_bad_requests( self ):
        resp = self.post( '/users/%s/props/'%username2, {} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertDictEqual( self.user1.get_properties(), {} )
        self.assertDictEqual( self.user2.get_properties(), {} )
        
        resp = self.post( '/users/%s/props/'%username2, {'foo': 'bar'} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertDictEqual( self.user1.get_properties(), {} )
        self.assertDictEqual( self.user2.get_properties(), {} )
        
        resp = self.post( '/users/%s/props/'%username2, {'foo': 'bar', 'prop': propkey3,
                                                            'value': propval3} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertDictEqual( self.user1.get_properties(), {} )
        self.assertDictEqual( self.user2.get_properties(), {} )

class GetPropertyTests( PropertyTests ): # GET /users/<user>/props/<prop>/
    def test_user_doesnt_exist( self ):
        resp = self.get( '/users/%s/props/%s/'%(username3, propkey1) )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_property_doesnt_exist( self ):
        resp = self.get( '/users/%s/props/%s/'%(username1, propkey1) )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'property' )
        
    def test_get_property( self ):
        self.user1.add_property( propkey1, propval1 )
        
        resp = self.get( '/users/%s/props/%s/'%(username1, propkey1) )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertEquals( self.parse( resp, 'str' ), propval1 ) # return old value
        
        # check that user2 doesn't have it:
        resp = self.get( '/users/%s/props/%s/'%(username2, propkey1) )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'property' )
      
class SetPropertyTests( PropertyTests ): # PUT /users/<user>/props/<prop>/
    def test_user_doesnt_exist( self ):
        resp = self.put( '/users/%s/props/%s/'%(username3, propkey1), {'value': propval1} )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
        # assert that no property has been created:
        self.assertEquals( list( Property.objects.all()), [] )
        
    def test_set_new_property( self ):
        # set a property
        resp = self.put( '/users/%s/props/%s/'%(username1, propkey1), {'value': propval1} )
        self.assertEquals( resp.status_code, httplib.CREATED )
        self.assertEquals( user_get( username1 ).property_set.get( key=propkey1 ).value, propval1 )
        self.assertFalse( user_get( username2 ).property_set.filter( key=propkey1 ).exists() )
        
    def test_set_existing_property( self ):
        self.user1.add_property( propkey1, propval1 )
        
        # set a property again and assert that it returns the old value:
        resp = self.put( '/users/%s/props/%s/'%(username1, propkey1), {'value': propval2} )
        self.assertEquals( resp.status_code, httplib.OK )
        self.assertEquals( self.parse( resp, 'str' ), propval1 ) # old value returned
        self.assertEquals( user_get( username1 ).property_set.get( key=propkey1 ).value, propval2 )
        self.assertFalse( user_get( username2 ).property_set.filter( key=propkey1 ).exists() )
        
    def test_bad_request( self ):
        # do some bad request tests:
        resp = self.put( '/users/%s/props/%s/'%(username1, propkey1), {} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( list( Property.objects.all().values_list( 'key', 'value' )) , [] )
        
        resp = self.put( '/users/%s/props/%s/'%(username1, propkey1), {'foo': 'bar'} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( list( Property.objects.all().values_list( 'key', 'value' )), [] )
        
        resp = self.put( '/users/%s/props/%s/'%(username1, propkey1), {'value': propkey3, 'foo':'bar'} )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertEquals( list( Property.objects.all().values_list( 'key', 'value' )), [] )
        
class DeletePropertyTests( PropertyTests ): # DELETE /users/<user>/props/<prop>/
    def test_user_doesnt_exist( self ):
        resp = self.delete( '/users/%s/props/%s/'%(username3, propkey1), )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'user' )
        
    def test_property_doesnt_exist( self ):
        resp = self.delete( '/users/%s/props/%s/'%(username1, propkey1), )
        self.assertEquals( resp.status_code, httplib.NOT_FOUND )
        self.assertEqual( resp['Resource-Type'], 'property' )
        
    def test_delete_property( self ):
        self.user1.add_property( propkey1, propval1 )
        self.user1.add_property( propkey2, propval2 )
        
        resp = self.delete( '/users/%s/props/%s/'%(username1, propkey1), )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertItemsEqual( self.user1.property_set.values_list( 'key', 'value' ).all(),
                          [(propkey2, propval2)] )
        
    def test_cross_user( self ):
        # two users have properties with the same key, we verify that deleting one doesn't delete
        # the other:
        self.user1.add_property( propkey1, propval1 )
        self.user2.add_property( propkey1, propval1 )
        
        resp = self.delete( '/users/%s/props/%s/'%(username1, propkey1), )
        self.assertEquals( resp.status_code, httplib.NO_CONTENT )
        self.assertItemsEqual( list( self.user1.property_set.all() ), [] )
        self.assertItemsEqual( self.user2.property_set.values_list( 'key', 'value' ).all(),
                          [(propkey1, propval1)] )