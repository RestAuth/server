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

try:
    import httplib as httpclient  # python 2.x
except ImportError:
    from http import client as httpclient  # python 3.x

#from unittest import skipUnless

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import load_hashers
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.test.utils import override_settings

from RestAuth.common.errors import PropertyNotFound
from RestAuth.common.testdata import RestAuthTest
from RestAuth.common.testdata import RestAuthTestBase
from RestAuth.common.testdata import password1
from RestAuth.common.testdata import password2
from RestAuth.common.testdata import password3
from RestAuth.common.testdata import property_backend
from RestAuth.common.testdata import propkey1
from RestAuth.common.testdata import propkey2
from RestAuth.common.testdata import propkey3
from RestAuth.common.testdata import propval1
from RestAuth.common.testdata import propval2
from RestAuth.common.testdata import propval3
from RestAuth.common.testdata import propval4
from RestAuth.common.testdata import propval5
from RestAuth.common.testdata import user_backend
from RestAuth.common.testdata import username1
from RestAuth.common.testdata import username2
from RestAuth.common.testdata import username3


class GetUsersTests(RestAuthTest):  # GET /users/
    def test_get_empty_users(self):
        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [])

    def test_get_one_user(self):
        self.create_user(username1, password1)

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1])

    def test_get_two_users(self):
        self.create_user(username1, password1)
        self.create_user(username2, password1)

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2])


class AddUserTests(RestAuthTest):  # POST /users/
    def tearDown(self):
        super(AddUserTests, self).tearDown()
        property_backend.testTearDown()

    def get_usernames(self):
        return user_backend.list()

    def test_add_user(self):
        resp = self.post('/users/', {'user': username1, 'password': password1})

        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertEqual(self.get_usernames(), [username1])
        self.assertPassword(username1, password1)
        user = user_backend.get(username1)
        self.assertProperties(user, {})

    def test_add_two_users(self):
        resp = self.post('/users/', {'user': username1, 'password': password1})
        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertEqual(self.get_usernames(), [username1])
        self.assertPassword(username1, password1)
        self.assertFalsePassword(username1, password2)
        user1 = user_backend.get(username1)
        self.assertProperties(user1, {})

        resp = self.post('/users/', {'user': username2, 'password': password2})
        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertEqual(self.get_usernames(), [username1, username2])
        user2 = user_backend.get(username2)
        self.assertProperties(user2, {})

        self.assertPassword(username1, password1)
        self.assertFalsePassword(username1, password2)
        self.assertPassword(username2, password2)
        self.assertFalsePassword(username2, password1)

    def test_add_user_twice(self):
        self.assertEqual(self.get_usernames(), [])
        resp = self.post('/users/', {'user': username1, 'password': password1})
        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertEqual(self.get_usernames(), [username1])
        user = user_backend.get(username1)
        self.assertProperties(user, {})

        self.assertPassword(username1, password1)
        self.assertFalsePassword(username1, password2)

        # add again:
        resp = self.post('/users/', {'user': username1, 'password': password2})
        self.assertEqual(resp.status_code, httpclient.CONFLICT)
        self.assertEqual(self.get_usernames(), [username1])

        # check that we still have the old password and properties:
        self.assertPassword(username1, password1)
        self.assertFalsePassword(username1, password2)

    def test_add_user_no_pass(self):
        resp = self.post('/users/', {'user': username1})
        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertEqual(self.get_usernames(), [username1])
        self.assertFalsePassword(username1, '')
        self.assertFalsePassword(username1, None)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, password2)
        self.assertProperties(user_backend.get(username1), {})

        resp = self.post('/users/', {'user': username2, 'password': ''})
        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertEqual(self.get_usernames(), [username1, username2])
        user = user_backend.get(username2)
        self.assertFalsePassword(username2, '')
        self.assertFalsePassword(username2, None)
        self.assertFalsePassword(username2, password1)
        self.assertFalsePassword(username2, password2)
        self.assertProperties(user, {})

        resp = self.post('/users/', {'user': username3, 'password': None})
        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertItemsEqual(
            self.get_usernames(), [username1, username2, username3])
        user = user_backend.get(username3)
        self.assertFalsePassword(username3, '')
        self.assertFalsePassword(username3, None)
        self.assertFalsePassword(username3, password1)
        self.assertFalsePassword(username3, password2)
        self.assertProperties(user, {})

    def test_add_user_with_property(self):
        resp = self.post('/users/', {'user': username1, 'properties': {
            propkey1: propval1
        }})

        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertEqual(self.get_usernames(), [username1])

        user = user_backend.get(username1)
        self.assertProperties(user, {propkey1: propval1})

    def test_add_user_with_properties(self):
        props = {propkey1: propval1, propkey2: propval2}
        resp = self.post('/users/', {'user': username1, 'properties': props})
        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertProperties(user_backend.get(username1), props)

    def test_bad_requests(self):
        self.assertEqual(self.get_usernames(), [])

        resp = self.post('/users/', {'password': 'foobar'})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertEqual(self.get_usernames(), [])

        resp = self.post('/users/', {})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertEqual(self.get_usernames(), [])

        resp = self.post('/users/', {
            'userasdf': username1, 'passwordasdf': 'foobar'
        })
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertEqual(self.get_usernames(), [])

    def test_add_invalid_username(self):
        username = 'foo/bar'
        resp = self.post('/users/', {'user': username, 'password': password1})
        self.assertEqual(resp.status_code, httpclient.PRECONDITION_FAILED)
        self.assertEqual(self.get_usernames(), [])

        username = 'foo:bar'
        resp = self.post('/users/', {'user': username, 'password': password1})
        self.assertEqual(resp.status_code, httpclient.PRECONDITION_FAILED)
        self.assertEqual(self.get_usernames(), [])

    def test_add_user_with_long_username(self):
        username = 'abc' * 200
        resp = self.post('/users/', {'user': username})
        self.assertEqual(resp.status_code, httpclient.PRECONDITION_FAILED)
        self.assertEqual(self.get_usernames(), [])


class UserTests(RestAuthTest):
    def setUp(self):
        RestAuthTest.setUp(self)

        # two users, so we can make sure nothing leaks to the other user
        self.user1 = self.create_user(username1, password1)
        self.user2 = self.create_user(username2, password2)


class UserExistsTests(UserTests):  # GET /users/<user>/
    def test_user_exists(self):
        resp = self.get('/users/%s/' % username1)
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)

        resp = self.get('/users/%s/' % username2)
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)

        resp = self.get('/users/%s/' % username3)
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')


class VerifyPasswordsTest(UserTests):  # POST /users/<user>/
    def test_user_doesnt_exist(self):
        resp = self.post('/users/%s/' % username3, {'password': 'foobar'})
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_verify_password(self):
        resp = self.post('/users/%s/' % username1, {'password': password1})
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)

        resp = self.post('/users/%s/' % username2, {'password': password2})
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)

    def test_verify_wrong_password(self):
        resp = self.post('/users/%s/' % username1, {'password': 'wrong'})
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

        resp = self.post('/users/%s/' % username2, {'password': 'wrong'})
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_verify_disabled_password(self):
        user3 = self.create_user(username3, None)

        resp = self.post('/users/%s/' % username3, {'password': 'wrong'})
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')
        resp = self.post('/users/%s/' % username3, {'password': ''})
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')
        resp = self.post('/users/%s/' % username3, {'password': None})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)

    def test_bad_requests(self):
        resp = self.post('/users/%s/' % username1, {})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)

        resp = self.post('/users/%s/' % username1, {'foo': 'bar'})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)

        resp = self.post('/users/%s/' % username1,
                         {'password': 'foobar', 'foo': 'bar'})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)


class ChangePasswordsTest(UserTests):  # PUT /users/<user>/
    def test_user_doesnt_exist(self):
        resp = self.put('/users/%s/' % username3, {'password': password3})
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_change_password(self):
        resp = self.put('/users/%s/' % username1, {'password': password3})
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, password2)
        self.assertPassword(username1, password3)

        # check user2, just to be sure:
        self.assertFalsePassword(username2, password1)
        self.assertPassword(username2, password2)
        self.assertFalsePassword(username2, password3)

    def test_disable_password(self):
        resp = self.put('/users/%s/' % username1, {})
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, '')
        self.assertFalsePassword(username1, None)

        resp = self.put('/users/%s/' % username1, {'password': ''})
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, '')
        self.assertFalsePassword(username1, None)

        resp = self.put('/users/%s/' % username1, {'password': None})
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, '')
        self.assertFalsePassword(username1, None)

    def test_bad_requests(self):
        resp = self.put('/users/%s/' % username1, {'foo': password2})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertPassword(username1, password1)

        resp = self.put('/users/%s/' % username1,
                        {'password': password3, 'foo': 'bar'})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertPassword(username1, password1)


class DeleteUserTest(UserTests):  # DELETE /users/<user>/
    def test_user_doesnt_exist(self):
        resp = self.delete('/users/%s/' % username3)
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_delete_user(self):
        resp = self.delete('/users/%s/' % username1)
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)
        self.assertFalse(user_backend.exists(username1))
        self.assertTrue(user_backend.exists(username2))


class PropertyTests(RestAuthTest):
    """
    Superclass for tests on
    ``/users/<user>/props/`` and ``/users/<user>/props/<prop>/``.
    """
    def setUp(self):
        RestAuthTest.setUp(self)

        # two users, so we can make sure nothing leaks to the other user
        self.user1 = self.create_user(username1, password1)
        self.user2 = self.create_user(username2, password2)

    def tearDown(self):
        super(PropertyTests, self).tearDown()
        property_backend.testTearDown()


class GetAllPropertiesTests(PropertyTests):  # GET /users/<user>/props/
    def parse(self, response, typ):
        body = super(GetAllPropertiesTests, self).parse(response, typ)
        del body['date joined']
        return body

    def test_user_doesnot_exist(self):
        resp = self.get('/users/%s/props/' % username3)
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_get_no_properties(self):
        resp = self.get('/users/%s/props/' % username1)
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

    def test_get_single_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)

        resp = self.get('/users/%s/props/' % username1)
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {propkey1: propval1})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

    def test_get_two_properties(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)
        property_backend.create(user=self.user1, key=propkey2, value=propval2)

        resp = self.get('/users/%s/props/' % username1)
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertDictEqual(self.parse(resp, 'dict'),
                             {propkey1: propval1, propkey2: propval2})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

    def test_get_multiple_properties(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)
        property_backend.create(user=self.user1, key=propkey2, value=propval2)
        property_backend.create(user=self.user2, key=propkey3, value=propval3)

        resp = self.get('/users/%s/props/' % username1)
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertDictEqual(self.parse(resp, 'dict'),
                             {propkey1: propval1, propkey2: propval2})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {propkey3: propval3})


class CreatePropertyTests(PropertyTests):  # POST /users/<user>/props/
    def test_user_doesnt_exist(self):
        resp = self.post('/users/%s/props/' % username3,
                         {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_create_property(self):
        resp = self.post('/users/%s/props/' % username1,
                         {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, httpclient.CREATED)

        self.assertProperties(self.user1, {propkey1: propval1})
        self.assertProperties(self.user2, {})

        # we create a second property
        resp = self.post('/users/%s/props/' % username1,
                         {'prop': propkey2, 'value': propval2})
        self.assertEqual(resp.status_code, httpclient.CREATED)

        self.assertProperties(self.user1,
                             {propkey1: propval1, propkey2: propval2})
        self.assertProperties(self.user2, {})

        # and a property for second user:
        resp = self.post('/users/%s/props/' % username2,
                         {'prop': propkey3, 'value': propval3})
        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertProperties(self.user1,
                             {propkey1: propval1, propkey2: propval2})
        self.assertProperties(self.user2, {propkey3: propval3})

    def test_create_existing_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)

        resp = self.post('/users/%s/props/' % username1,
                         {'prop': propkey1, 'value': propval2})
        self.assertEqual(resp.status_code, httpclient.CONFLICT)

        self.assertProperties(self.user1, {propkey1: propval1})
        self.assertProperties(self.user2, {})

    def test_create_invalid_property(self):
        resp = self.post('/users/%s/props/' % username1,
                         {'prop': "foo:bar", 'value': propval2})
        self.assertEqual(resp.status_code, httpclient.PRECONDITION_FAILED)
        self.assertProperties(self.user1, {})

    def test_bad_requests(self):
        resp = self.post('/users/%s/props/' % username2, {})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertProperties(self.user1, {})
        self.assertProperties(self.user2, {})

        resp = self.post('/users/%s/props/' % username2, {'foo': 'bar'})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertProperties(self.user1, {})
        self.assertProperties(self.user2, {})

        resp = self.post('/users/%s/props/' % username2, {
            'foo': 'bar', 'prop': propkey3, 'value': propval3
        })
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertProperties(self.user1, {})
        self.assertProperties(self.user2, {})


class SetMultiplePropertiesTests(PropertyTests):
    def test_user_doesnt_exist(self):
        resp = self.put('/users/%s/props/' % username3,
                        {propkey1: propval1, propkey2: propval2})
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_no_property(self):
        resp = self.put('/users/%s/props/' % username1, {})
        self.assertProperties(self.user1, {})

    def test_create_one_property(self):
        testdict = {propkey1: propval1}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

    def test_create_two_properties(self):
        testdict = {propkey1: propval1, propkey2: propval2}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

    def test_create_three_properties(self):
        testdict = {propkey1: propval1, propkey2: propval2, propkey3: propval3}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

    def test_set_one_property(self):
        testdict = {propkey1: propval1}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

        testdict = {propkey1: propval2}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

    def test_set_two_properties(self):
        testdict = {propkey1: propval1, propkey2: propval2}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

        testdict = {propkey1: propval3, propkey2: propval4}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

    def test_set_three_properties(self):
        testdict = {propkey1: propval1, propkey2: propval2, propkey3: propval3}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

        testdict = {propkey1: propval2, propkey2: propval5, propkey3: propval4}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

    def test_mix_set_and_create(self):
        testdict = {propkey1: propval1}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)

        testdict = {propkey1: propval1, propkey2: propval2}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertProperties(self.user1, testdict)


class GetPropertyTests(PropertyTests):  # GET /users/<user>/props/<prop>/
    def test_user_doesnt_exist(self):
        resp = self.get('/users/%s/props/%s/' % (username3, propkey1))
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_property_doesnt_exist(self):
        resp = self.get('/users/%s/props/%s/' % (username1, propkey1))
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'property')

    def test_get_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)

        resp = self.get('/users/%s/props/%s/' % (username1, propkey1))
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertEqual(self.parse(resp, 'str'), propval1)

        # check that user2 doesn't have it:
        resp = self.get('/users/%s/props/%s/' % (username2, propkey1))
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'property')


class SetPropertyTests(PropertyTests):  # PUT /users/<user>/props/<prop>/
    def test_user_doesnt_exist(self):
        resp = self.put(
            '/users/%s/props/%s/' % (username3, propkey1), {'value': propval1})
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_set_new_property(self):
        # set a property
        resp = self.put(
            '/users/%s/props/%s/' % (username1, propkey1), {'value': propval1})
        self.assertEqual(resp.status_code, httpclient.CREATED)
        self.assertEqual(property_backend.get(self.user1, propkey1), propval1)
        self.assertRaises(PropertyNotFound,
                          property_backend.get, self.user2, propkey1)

    def test_set_existing_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)

        # set a property again and assert that it returns the old value:
        resp = self.put(
            '/users/%s/props/%s/' % (username1, propkey1), {'value': propval2})
        self.assertEqual(resp.status_code, httpclient.OK)
        self.assertEqual(self.parse(resp, 'str'), propval1)
        self.assertEqual(property_backend.get(self.user1, propkey1), propval2)
        self.assertRaises(PropertyNotFound,
                          property_backend.get, self.user2, propkey1)

    def test_bad_request(self):
        # do some bad request tests:
        resp = self.put('/users/%s/props/%s/' % (username1, propkey1), {})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertProperties(self.user1, {})

        resp = self.put('/users/%s/props/%s/' % (username1, propkey1),
                        {'foo': 'bar'})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertProperties(self.user1, {})

        resp = self.put('/users/%s/props/%s/' % (username1, propkey1),
                        {'value': propkey3, 'foo': 'bar'})
        self.assertEqual(resp.status_code, httpclient.BAD_REQUEST)
        self.assertProperties(self.user1, {})


class DeletePropertyTests(PropertyTests):  # DELETE /users/<user>/props/<prop>/
    def test_user_doesnt_exist(self):
        resp = self.delete('/users/%s/props/%s/' % (username3, propkey1),)
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_property_doesnt_exist(self):
        resp = self.delete('/users/%s/props/%s/' % (username1, propkey1),)
        self.assertEqual(resp.status_code, httpclient.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'property')

    def test_delete_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)
        property_backend.create(user=self.user1, key=propkey2, value=propval2)

        resp = self.delete('/users/%s/props/%s/' % (username1, propkey1),)
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)
        self.assertProperties(self.user1, {propkey2: propval2})

    def test_cross_user(self):
        # two users have properties with the same key, we verify that deleting
        # one doesn't delete the other:
        property_backend.create(user=self.user1, key=propkey1, value=propval1)
        property_backend.create(user=self.user2, key=propkey1, value=propval1)

        resp = self.delete('/users/%s/props/%s/' % (username1, propkey1),)
        self.assertEqual(resp.status_code, httpclient.NO_CONTENT)
        self.assertProperties(self.user1, {})
        self.assertProperties(self.user2, {propkey1: propval1})


class HashTestMixin(RestAuthTestBase):
    hashers = None
    algorithm = None
    testdata = None

    def setUp(self):
        # Required in Django 1.4, not in 1.5
        super(HashTestMixin, self).setUp()
        with self.settings(PASSWORD_HASHERS=self.hashers):
            load_hashers()

    def generate(self, data):
        return '%s$%s$%s' % (self.algorithm, data['salt'], data['hash'])

    @override_settings(MIN_PASSWORD_LENGTH=1)
    def test_testdata(self):
        for password, data in self.testdata.items():
            generated = make_password(password, data['salt'],
                                      hasher=self.algorithm)
            self.assertTrue(generated.startswith('%s$' % self.algorithm))
            self.assertEqual(generated, self.generate(data))

            # twice to test possible override:
            self.assertTrue(check_password(password, generated))
            self.assertTrue(check_password(password, generated))

    @override_settings(MIN_PASSWORD_LENGTH=1)
#    @skipUnless(settings.USER_BACKEND == 'RestAuth.backends.django_backend.DjangoUserBackend', '')
    def test_backend(self):
        if settings.USER_BACKEND != 'RestAuth.backends.django_backend.DjangoUserBackend':
            # we do not use skipUnless because its introduced in python2.7.
            return

        # test password during creation:
        for password, data in self.testdata.items():
            user = user_backend.create(username=username1,
                                       password=password,
                                       property_backend=property_backend)
            self.assertTrue(user.password.startswith('%s$' % self.algorithm))
            self.assertTrue(user_backend.check_password(username1, password))

            user_backend.remove(username=username1)

        # test password for set_password:
        for password, data in self.testdata.items():
            user = user_backend.create(username=username1,
                                       property_backend=property_backend)
            user_backend.set_password(username=username1, password=password)
            self.assertTrue(user_backend.check_password(username1, password))
            self.assertTrue(user_backend.check_password(username1, password))

            user = user_backend.get(username1)
            self.assertTrue(user.password.startswith('%s$' % self.algorithm))
            self.assertTrue(check_password(password, user.password))

            user_backend.remove(username=username1)


@override_settings(PASSWORD_HASHERS=('RestAuth.common.hashers.PhpassHasher',))
class PhpassTest(HashTestMixin, TestCase):
    hashers = ('RestAuth.common.hashers.PhpassHasher',)
    algorithm = 'phpass'

    testdata = {
        '1': {'salt': 'BRKt3c7uu', 'hash': 'L2aesAJo1CQjoxGzyPdWr1'},
        '12': {'salt': 'BmM42e2cS', 'hash': '91zgpkpgP89xe3OeAIpT40'},
        '123': {'salt': 'BP58lS6kJ', 'hash': '916dAnpf26hPCQI0whXsO1'},
        '1234': {'salt': 'BpAYOjl1P', 'hash': '9fPA4pIKjt/q66QpFrsDW1'},
        '12345': {'salt': 'BmuukKnan', 'hash': 'h1XwbmUT6PkxpEr/9pOI00'},
        '123456': {'salt': 'Bc9fhNMWG', 'hash': 'FRLOT7ZpY6TAYoSf.bIdD0'},
        '1234567': {'salt': 'BlT2XNtZD', 'hash': 'pirchpCqdGmbWRenYNpzE.'},
        '12345678': {'salt': 'BqXel7ZCN', 'hash': '22KlBpQogL5PJC52hHuD91'},
        'if9prH3F5Y57': {'salt': 'Bv5IkQCrO',
                         'hash': '7LFot6oQrkBy/ToD1kLvt.'},
        '1YqgPVFITEyt': {'salt': 'BKhwIDVD/',
                         'hash': 'BfqOTbzU1HsuBbSvZdENs.'},
        'Ji67AxtXzhKK': {'salt': 'BK0P5khBm',
                         'hash': 's9.dRMDutvTii5E.gT.Ji1'},
        'riyBxGIL18vf': {'salt': 'BOkvZdLFu',
                         'hash': 'YEkYAaxG0g/mUladF0dNO/'},
        'WvhQMorIXqUX': {'salt': 'BoDae5Q0Y',
                         'hash': 'fXvarDorOTb.fj44OqbOc1'},
    }

    def generate(self, data):
        return '%s$P$%s%s' % (self.algorithm, data['salt'], data['hash'])


@override_settings(PASSWORD_HASHERS=('RestAuth.common.hashers.Drupal7Hasher',))
class Drupal7Test(HashTestMixin, TestCase):
    hashers = ('RestAuth.common.hashers.Drupal7Hasher',)
    algorithm = 'drupal7'

    testdata = {
        '1': {'salt': 'DtfbJVKBh',
              'hash': 'lHmYDIMN7WChUUvEhATGnflurtH7c46/4I9Mocpi.0O'},
        '12': {'salt': 'D/Ke05Og0',
               'hash': 'fQ0NFG7OzsgIoxuZ2bjHvLr4MjoLq3nHVkleR/qTDd5'},
        '123': {'salt': 'Dl0ruon0i',
                'hash': 'SMu2oThzN.pbFPdtD5Sh67WHN92WU/tx9rJgZyel/LT'},
        '1234': {'salt': 'DvL6XrqV1',
                 'hash': '6VBeRqFZlu0kdVlCXaF4LbSfTbQkpQ5QY1bc3wDNiZq'},
        '12345': {'salt': 'DDcFBLTez',
                  'hash': 'B1zxDDL5TK5v7iVqlP0H4H8gv1CbGTbAAtwyO//e1Rg'},
        '123456': {'salt': 'DoxC.Busk',
                   'hash': 'MRu2HSdCh29u0ZTJhETlEaxyH/JUIvtQ7oD2Rkxnl3c'},
        '1234567': {'salt': 'DE/joQlAl',
                    'hash': 'd8eZk/MB65Wb7Mzihm2M/WEfAYthl2aPTjSSBLJ/wX5'},
        '12345678': {'salt': 'D/YGN6xK5',
                     'hash': '0wPvroaZq4QLT.vLCbt0JGMAPSCYxcN6BO4uSxjRrux'},
        's8zm3mPH88mY': {
            'salt': 'DzGBWhU4E',
            'hash': 'QifJeFvwTPvJvc03yvOrI1PebgOj9GCAZvoKMtRVmuZ',
        },
        'dfi31ps18XaR': {
            'salt': 'DHFKOWOc.',
            'hash': '2pgOGy5s59k1WzhTiMUcHrdPlIzFnbuEK7m54j2zrkT',
        },
        'izfqISu3hVrx': {
            'salt': 'Dnspf7cF3',
            'hash': '.Pk793BzmyMtonIlWJp3Vh8Zix0wMCV.j.KCAGamoz0',
        },
        'rGUo7cpMTv1f': {
            'salt': 'Dcm.rOynf',
            'hash': 'SWVgqarUIk9Vemk/txNQbaPaWJqTPR4gcSrHMor4o8K',
        },
        'qJreivhrj04Y': {
            'salt': 'DorDKO73p',
            'hash': 'PICBMd2BgWbowvDk3y7L159JaYmjvSV/hyQJnHGmgak',
        },
    }

    def generate(self, data):
        return '%s$S$%s%s' % (self.algorithm, data['salt'], data['hash'])


@override_settings(PASSWORD_HASHERS=('RestAuth.common.hashers.Sha512Hasher',))
class Sha512Test(HashTestMixin, TestCase):
    hashers = ('RestAuth.common.hashers.Sha512Hasher',)
    algorithm = 'sha512'

    testdata = {
        '0123456': {'salt': 'NDuF22tTDpgEWj0T',
                    'hash': '2006d00c8168f3a2520c24ffee25cb099dbf9ceea7e5f2286bfb86fb02c1be51d3322a162aee1a4bd5908c4468346f45a98a959128ddd5eb106aaad4d9b2ecdd'},
        '01234567': {'salt': 'dWOGt5pdhcBabI7T',
                     'hash': '6c560f8634f83fc127d27cfb3a3394f01045565874da8697aaef2ac599903e63eccf93bbda055bfb8504f1eec5d4388e165d7155418c646a061f4475bdd64154'},
        '012345678': {'salt': 'tPokxHTJSrKcOehr',
                     'hash': '5ae80da515729596cf4d4b36092e063bd38c75bd9de0a1372453a38dafdaa16bd0719e632769806c153234e853c4db22a39be0ca54e944efa5ab01b518921211'},
        '0123456789': {'salt': 'vh5rweyXH150n8vX',
                      'hash': '7cba9c9fd63e4cccc06c6715f1ccc06947dc00605bba01d636440f3f3e4b967b1de369aa5ad91d57e6a8aac094d9987ffb8d68b8a80b21fef767bcb57537b012'},
        '01234567890': {'salt': 'ehDkCua04OasAdMY',
                        'hash': '12cf5d5140f2a98b1caa58e20489ca487872e49831bef25a8523c2f159ed198a56cf2738391cd26ce3e9b3a59470e1d8226ab7724a706e761675884f2078a6a8'},
    }


@override_settings(
    PASSWORD_HASHERS=('RestAuth.common.hashers.MediaWikiHasher',))
class MediaWikiTest(HashTestMixin, TestCase):
    hashers = ('RestAuth.common.hashers.MediaWikiHasher',)
    algorithm = 'mediawiki'

    testdata = {
        "0": {"salt": "4891a58e",
              "hash": "222ecf008e098295058d0c9a77e19d16"},
        "012": {"salt": "7bb9c41a",
                "hash": "f72fbb4126a0002d88cb4afc62980d49"},
        "0123": {"salt": "e4121fde",
                 "hash": "2de7c06ecfee2468cc0f6cf345632d29"},
        "01234": {"salt": "99739c15",
                  "hash": "5c1ddaa0fa981ac651c6bac72f640e44"},
        "012345": {"salt": "9650ce2d",
                   "hash": "2ad8888099fe7ce36d84c1046638f261"},
        "0123456": {"salt": "d0027595",
                    "hash": "49a25052a0690e607c1f7d103c2b51b9"},
        "01234567": {"salt": "eec0c833",
                     "hash": "971a19cefb858a481e7b0e36137774da"},
        "012345678": {"salt": "fb74cdba",
                      "hash": "9e562f64b90a6445de607f30dc745c7d"},
        "0123456789": {"salt": "02828b87",
                       "hash": "555f6f62e646afc840b1995d0467ef06"},
    }


@override_settings(PASSWORD_HASHERS=('RestAuth.common.hashers.Apr1Hasher',))
class Apr1Test(HashTestMixin, TestCase):
    hashers = ('RestAuth.common.hashers.Apr1Hasher',)
    algorithm = 'apr1'

    testdata = {
        "f": {"hash": "wencZ6WkOMvuOANC/A8LZ0", "salt": "nErdosRy"},
        "fo": {"hash": "Vyc4Thuvc/YAbWYb1nVI70", "salt": "1aigqzQz"},
        "foo": {"hash": "cXr93EItT.sxzwewzWX4p.", "salt": "c.aI4ooC"},
        "foob": {"hash": "jN4YoWkxbtBI8D8d/Xoo3.", "salt": "wcPr1Vxv"},
        "fooba": {"hash": "Tn2C7XgOdv6v45XbC8TNn/", "salt": "nQp8UKRJ"},
        "foobar": {"hash": "XD2jiMfDOvzldmLpJl9SO.", "salt": "ilSj3Uel"},
        "foobar0": {"hash": "94YS3btM0C/5CiUvCOW.s/", "salt": "hrTvU.wk"},
        "foobar01": {"hash": "4Pqs5OTqXx3IGF3pm7QLv1", "salt": "EytZabM0"},
        "foobar012": {"hash": "eLFTYKqrZaXlLoUY6CziS/", "salt": "EkOE4ywR"},
        "foobar0123": {"hash": "K1k6x/RVk92AmiWnAFdEj.", "salt": "pMAaLcxe"},
        "foobar01234": {"hash": "PAtaCCc4kqruXb0NLoRTg0", "salt": "sAEmwZJG"},
        "foobar012345": {"hash": "I9pT1Vx.CMEO6wqelEAOP0", "salt": "aQ.R.N4o"},
        "foobar0123456": {
            "hash": "G4zjuqUYGU6nFSxPFyO4x0", "salt": "HvbXrlI/"},
        "foobar01234567": {
            "hash": "cVAXAQ42OPeHSC3SNSOHS/", "salt": "TDF/0tAf"},
        "foobar012345678": {
            "hash": "HASHq302/S19PI.RLbb400", "salt": "zaKZEcLq"},
        "foobar0123456789": {
            "hash": "TzOmxdrHqe0HfwxIPXlU10", "salt": "NjALUYrK"},
        "foobar01234567890": {
            "hash": "aQ127rgKtHR098iUEgW.F1", "salt": "SJJuaEKa"},
        "foobar012345678901": {
            "hash": "TLkfRBIjGqjL4clR0873c1", "salt": "hDJaX1Sa"},
        "foobar0123456789012": {
            "hash": "1OIrHIzF.HOQ72wbcFWzU0", "salt": "HlBLH.DU"},
        "foobar01234567890123": {
            "hash": "hnBripG.5yMPXE4FJg7Np0", "salt": "snk9PtYt"},
        "foobar012345678901234": {
            "hash": "zbRB1BrZmWaFKJMqKyTum0", "salt": "NyCJRWye"},
        "foobar0123456789012345": {
            "hash": "UugUUu7D7pABxWg2p2ovc1", "salt": "c3tj3eYu"},
        "foobar01234567890123456": {
            "hash": "8iXmJONIozEPLup/2KgQp/", "salt": "tecrND8A"},
        "foobar012345678901234567": {
            "hash": "fx2Tly.fIvybOKAbtUWMN/", "salt": "JpSOF7qJ"},
        "foobar0123456789012345678": {
            "hash": "fGBumUrVrJ40UB/Q2K1lI.", "salt": "fS58gR6t"},
        "foobar01234567890123456789": {
            "hash": "bEsAOMdUIs1GNh5LLjlP1.", "salt": "PLG28sJA"},
        "foobar012345678901234567890": {
            "hash": "CmoV8ccWcCEzBV01Pq496/", "salt": "MM49C.Vs"},
        "foobar0123456789012345678901": {
            "hash": "2tGWA3NHFeGAEmSXZhYnR/", "salt": "9n8nToVo"},
        "foobar01234567890123456789012": {
            "hash": "1cyFn3QVsTQf5RID7O6wC.", "salt": "88x7/ARO"},
        "foobar012345678901234567890123": {
            "hash": "ADOeE2pC3SIrRPpj1wdJs/", "salt": "r/oMeWiA"},
        "foobar0123456789012345678901234": {
            "hash": "O6pOM0l0DEfJipuhQLk1u/", "salt": "hViGYCEr"},
        "foobar01234567890123456789012345": {
            "hash": "WcPoFDPY2hMpalN2bZibX.", "salt": "2QBHE4/Q"},
        "foobar012345678901234567890123456": {
            "hash": "BHCTbYz7NZZK4HAFuHLzG.", "salt": "knaM/8D4"},
        "foobar0123456789012345678901234567": {
            "hash": "QyzsGHXVFAEu1aO9rkphD0", "salt": "gfdWhcS7"},
        "foobar01234567890123456789012345678": {
            "hash": "Frfmzydl8OC7RrMbkTUY21", "salt": "v8oc0omI"},
        "foobar012345678901234567890123456789": {
            "hash": "ZvOpfsrYFSUgUwtVsCUBR0", "salt": "GAAPD33a"},
        "foobar0123456789012345678901234567890": {
            "hash": "D2ISHi8yEIL/0MzNWiDis.", "salt": "3Glrt6Oh"},
    }

    def setUp(self):
        super(Apr1Test, self).setUp()
