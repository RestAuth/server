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

import httplib

from django.conf import settings

from RestAuth.common.errors import PropertyNotFound
from RestAuth.common.decorators import override_settings
from RestAuth.common.testdata import (
    RestAuthTest,
    user_backend, property_backend,
    username1, username2, username3,
    password1, password2, password3,
    propkey1, propkey2, propkey3,
    propval1, propval2, propval3, propval4, propval5,
)

from Users.models import ServiceUser


class GetUsersTests(RestAuthTest):  # GET /users/
    def test_get_empty_users(self):
        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [])

    def test_get_one_user(self):
        self.create_user(username1, password1)

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1])

    def test_get_two_users(self):
        self.create_user(username1, password1)
        self.create_user(username2, password1)

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2])


class AddUserTests(RestAuthTest):  # POST /users/
    def tearDown(self):
        super(AddUserTests, self).tearDown()
        property_backend.testTearDown()

    def get_usernames(self):
        return user_backend.list()

    def test_add_user(self):
        resp = self.post('/users/', {'user': username1, 'password': password1})

        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertEqual(self.get_usernames(), [username1])
        self.assertPassword(username1, password1)
        user = user_backend.get(username1)
        self.assertProperties(user, {})

    def test_add_two_users(self):
        resp = self.post('/users/', {'user': username1, 'password': password1})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertEqual(self.get_usernames(), [username1])
        self.assertPassword(username1, password1)
        self.assertFalsePassword(username1, password2)
        user1 = user_backend.get(username1)
        self.assertProperties(user1, {})

        resp = self.post('/users/', {'user': username2, 'password': password2})
        self.assertEqual(resp.status_code, httplib.CREATED)
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
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertEqual(self.get_usernames(), [username1])
        user = user_backend.get(username1)
        self.assertProperties(user, {})

        self.assertPassword(username1, password1)
        self.assertFalsePassword(username1, password2)

        # add again:
        resp = self.post('/users/', {'user': username1, 'password': password2})
        self.assertEqual(resp.status_code, httplib.CONFLICT)
        self.assertEqual(self.get_usernames(), [username1])

        # check that we still have the old password and properties:
        self.assertPassword(username1, password1)
        self.assertFalsePassword(username1, password2)

    def test_add_user_no_pass(self):
        resp = self.post('/users/', {'user': username1})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertEqual(self.get_usernames(), [username1])
        self.assertFalsePassword(username1, '')
        self.assertFalsePassword(username1, None)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, password2)
        self.assertProperties(user_backend.get(username1), {})

        resp = self.post('/users/', {'user': username2, 'password': ''})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertEqual(self.get_usernames(), [username1, username2])
        user = user_backend.get(username2)
        self.assertFalsePassword(username2, '')
        self.assertFalsePassword(username2, None)
        self.assertFalsePassword(username2, password1)
        self.assertFalsePassword(username2, password2)
        self.assertProperties(user, {})

        resp = self.post('/users/', {'user': username3, 'password': None})
        self.assertEqual(resp.status_code, httplib.CREATED)
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

        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertEqual(self.get_usernames(), [username1])

        user = user_backend.get(username1)
        self.assertProperties(user, {propkey1: propval1})

    def test_add_user_with_properties(self):
        props = {propkey1: propval1, propkey2: propval2}
        resp = self.post('/users/', {'user': username1, 'properties': props})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertProperties(user_backend.get(username1), props)

    def test_bad_requests(self):
        self.assertEqual(self.get_usernames(), [])

        resp = self.post('/users/', {'password': 'foobar'})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertEqual(self.get_usernames(), [])

        resp = self.post('/users/', {})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertEqual(self.get_usernames(), [])

        resp = self.post('/users/', {
            'userasdf': username1, 'passwordasdf': 'foobar'
        })
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertEqual(self.get_usernames(), [])

    def test_add_invalid_username(self):
        username = 'foo/bar'
        resp = self.post('/users/', {'user': username, 'password': password1})
        self.assertEqual(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertEqual(self.get_usernames(), [])

        username = 'foo:bar'
        resp = self.post('/users/', {'user': username, 'password': password1})
        self.assertEqual(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertEqual(self.get_usernames(), [])

    def test_add_user_with_long_username(self):
        username = 'abc' * 200
        resp = self.post('/users/', {'user': username})
        self.assertEqual(resp.status_code, httplib.PRECONDITION_FAILED)
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
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)

        resp = self.get('/users/%s/' % username2)
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)

        resp = self.get('/users/%s/' % username3)
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')


class VerifyPasswordsTest(UserTests):  # POST /users/<user>/
    def test_user_doesnt_exist(self):
        resp = self.post('/users/%s/' % username3, {'password': 'foobar'})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_verify_password(self):
        resp = self.post('/users/%s/' % username1, {'password': password1})
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)

        resp = self.post('/users/%s/' % username2, {'password': password2})
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)

    def test_verify_wrong_password(self):
        resp = self.post('/users/%s/' % username1, {'password': 'wrong'})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

        resp = self.post('/users/%s/' % username2, {'password': 'wrong'})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_verify_disabled_password(self):
        user3 = self.create_user(username3, None)

        resp = self.post('/users/%s/' % username3, {'password': 'wrong'})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')
        resp = self.post('/users/%s/' % username3, {'password': ''})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')
        resp = self.post('/users/%s/' % username3, {'password': None})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)

    def test_bad_requests(self):
        resp = self.post('/users/%s/' % username1, {})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)

        resp = self.post('/users/%s/' % username1, {'foo': 'bar'})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)

        resp = self.post('/users/%s/' % username1,
                         {'password': 'foobar', 'foo': 'bar'})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)


class ChangePasswordsTest(UserTests):  # PUT /users/<user>/
    def test_user_doesnt_exist(self):
        resp = self.put('/users/%s/' % username3, {'password': password3})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_change_password(self):
        resp = self.put('/users/%s/' % username1, {'password': password3})
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, password2)
        self.assertPassword(username1, password3)

        # check user2, just to be sure:
        self.assertFalsePassword(username2, password1)
        self.assertPassword(username2, password2)
        self.assertFalsePassword(username2, password3)

    def test_disable_password(self):
        resp = self.put('/users/%s/' % username1, {})
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, '')
        self.assertFalsePassword(username1, None)

        resp = self.put('/users/%s/' % username1, {'password': ''})
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, '')
        self.assertFalsePassword(username1, None)

        resp = self.put('/users/%s/' % username1, {'password': None})
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)
        self.assertFalsePassword(username1, password1)
        self.assertFalsePassword(username1, '')
        self.assertFalsePassword(username1, None)

    def test_bad_requests(self):
        resp = self.put('/users/%s/' % username1, {'foo': password2})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertPassword(username1, password1)

        resp = self.put('/users/%s/' % username1,
                        {'password': password3, 'foo': 'bar'})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertPassword(username1, password1)


class DeleteUserTest(UserTests):  # DELETE /users/<user>/
    def test_user_doesnt_exist(self):
        resp = self.delete('/users/%s/' % username3)
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_delete_user(self):
        resp = self.delete('/users/%s/' % username1)
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)
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
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_get_no_properties(self):
        resp = self.get('/users/%s/props/' % username1)
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

    def test_get_single_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)

        resp = self.get('/users/%s/props/' % username1)
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {propkey1: propval1})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

    def test_get_two_properties(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)
        property_backend.create(user=self.user1, key=propkey2, value=propval2)

        resp = self.get('/users/%s/props/' % username1)
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'),
                             {propkey1: propval1, propkey2: propval2})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

    def test_get_multiple_properties(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)
        property_backend.create(user=self.user1, key=propkey2, value=propval2)
        property_backend.create(user=self.user2, key=propkey3, value=propval3)

        resp = self.get('/users/%s/props/' % username1)
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'),
                             {propkey1: propval1, propkey2: propval2})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {propkey3: propval3})


class CreatePropertyTests(PropertyTests):  # POST /users/<user>/props/
    def test_user_doesnt_exist(self):
        resp = self.post('/users/%s/props/' % username3,
                         {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_create_property(self):
        resp = self.post('/users/%s/props/' % username1,
                         {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, httplib.CREATED)

        self.assertProperties(self.user1, {propkey1: propval1})
        self.assertProperties(self.user2, {})

        # we create a second property
        resp = self.post('/users/%s/props/' % username1,
                         {'prop': propkey2, 'value': propval2})
        self.assertEqual(resp.status_code, httplib.CREATED)

        self.assertProperties(self.user1,
                             {propkey1: propval1, propkey2: propval2})
        self.assertProperties(self.user2, {})

        # and a property for second user:
        resp = self.post('/users/%s/props/' % username2,
                         {'prop': propkey3, 'value': propval3})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertProperties(self.user1,
                             {propkey1: propval1, propkey2: propval2})
        self.assertProperties(self.user2, {propkey3: propval3})

    def test_create_existing_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)

        resp = self.post('/users/%s/props/' % username1,
                         {'prop': propkey1, 'value': propval2})
        self.assertEqual(resp.status_code, httplib.CONFLICT)

        self.assertProperties(self.user1, {propkey1: propval1})
        self.assertProperties(self.user2, {})

    def test_create_invalid_property(self):
        resp = self.post('/users/%s/props/' % username1,
                         {'prop': "foo:bar", 'value': propval2})
        self.assertEqual(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertProperties(self.user1, {})

    def test_bad_requests(self):
        resp = self.post('/users/%s/props/' % username2, {})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertProperties(self.user1, {})
        self.assertProperties(self.user2, {})

        resp = self.post('/users/%s/props/' % username2, {'foo': 'bar'})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertProperties(self.user1, {})
        self.assertProperties(self.user2, {})

        resp = self.post('/users/%s/props/' % username2, {
            'foo': 'bar', 'prop': propkey3, 'value': propval3
        })
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertProperties(self.user1, {})
        self.assertProperties(self.user2, {})


class SetMultiplePropertiesTests(PropertyTests):
    def test_user_doesnt_exist(self):
        resp = self.put('/users/%s/props/' % username3,
                        {propkey1: propval1, propkey2: propval2})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
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
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_property_doesnt_exist(self):
        resp = self.get('/users/%s/props/%s/' % (username1, propkey1))
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'property')

    def test_get_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)

        resp = self.get('/users/%s/props/%s/' % (username1, propkey1))
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertEqual(self.parse(resp, 'str'), propval1)

        # check that user2 doesn't have it:
        resp = self.get('/users/%s/props/%s/' % (username2, propkey1))
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'property')


class SetPropertyTests(PropertyTests):  # PUT /users/<user>/props/<prop>/
    def test_user_doesnt_exist(self):
        resp = self.put(
            '/users/%s/props/%s/' % (username3, propkey1), {'value': propval1})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_set_new_property(self):
        # set a property
        resp = self.put(
            '/users/%s/props/%s/' % (username1, propkey1), {'value': propval1})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertEqual(property_backend.get(self.user1, propkey1), propval1)
        self.assertRaises(PropertyNotFound,
                          property_backend.get, self.user2, propkey1)

    def test_set_existing_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)

        # set a property again and assert that it returns the old value:
        resp = self.put(
            '/users/%s/props/%s/' % (username1, propkey1), {'value': propval2})
        self.assertEqual(resp.status_code, httplib.OK)
        self.assertEqual(self.parse(resp, 'str'), propval1)
        self.assertEqual(property_backend.get(self.user1, propkey1), propval2)
        self.assertRaises(PropertyNotFound,
                          property_backend.get, self.user2, propkey1)

    def test_bad_request(self):
        # do some bad request tests:
        resp = self.put('/users/%s/props/%s/' % (username1, propkey1), {})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertProperties(self.user1, {})

        resp = self.put('/users/%s/props/%s/' % (username1, propkey1),
                        {'foo': 'bar'})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertProperties(self.user1, {})

        resp = self.put('/users/%s/props/%s/' % (username1, propkey1),
                        {'value': propkey3, 'foo': 'bar'})
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertProperties(self.user1, {})


class DeletePropertyTests(PropertyTests):  # DELETE /users/<user>/props/<prop>/
    def test_user_doesnt_exist(self):
        resp = self.delete('/users/%s/props/%s/' % (username3, propkey1),)
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_property_doesnt_exist(self):
        resp = self.delete('/users/%s/props/%s/' % (username1, propkey1),)
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'property')

    def test_delete_property(self):
        property_backend.create(user=self.user1, key=propkey1, value=propval1)
        property_backend.create(user=self.user1, key=propkey2, value=propval2)

        resp = self.delete('/users/%s/props/%s/' % (username1, propkey1),)
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)
        self.assertProperties(self.user1, {propkey2: propval2})

    def test_cross_user(self):
        # two users have properties with the same key, we verify that deleting
        # one doesn't delete the other:
        property_backend.create(user=self.user1, key=propkey1, value=propval1)
        property_backend.create(user=self.user2, key=propkey1, value=propval1)

        resp = self.delete('/users/%s/props/%s/' % (username1, propkey1),)
        self.assertEqual(resp.status_code, httplib.NO_CONTENT)
        self.assertProperties(self.user1, {})
        self.assertProperties(self.user2, {propkey1: propval1})


class HashTest(RestAuthTest):

    @override_settings(MIN_PASSWORD_LENGTH=1)
    @override_settings(MIN_USERNAME_LENGTH=1)
    def test_crypt(self):
        testdata = {
            "f": {"hash": "zByHy85N5JE", "salt": "LG"},
            "fo": {"hash": "Lb4p57NVOh6", "salt": "qO"},
            "foo": {"hash": "SOM3CYj26Xk", "salt": "L/"},
            "foob": {"hash": "6J6SsDmmvPE", "salt": "fq"},
            "fooba": {"hash": "45YY/lBbQL.", "salt": "EG"},
            "foobar": {"hash": "5RKNB0QSl4g", "salt": "wC"},
            "foobar1": {"hash": "3.K3kCyb2AA", "salt": "st"},
            "foobar12": {"hash": "LbMAd.nZIv2", "salt": "ca"},
            "foobar123": {"hash": "9yA..KnYzIk", "salt": "s0"},
            "foobar1234": {"hash": "FOG2CHhzJm.", "salt": "SF"},
            "foobar12345": {"hash": "uqrrlepaCqE", "salt": "vB"},
            "foobar123456": {"hash": "44fvIAOpK5U", "salt": "ep"},
            "foobar1234567": {"hash": "TWg6AU5FFN6", "salt": "T."},
            "foobar12345678": {"hash": "KbFo0bhBYRs", "salt": "FF"},
            "foobar123456789": {"hash": "exX507cNB0.", "salt": "TU"},
            "foobar1234567890": {"hash": "FITBq2CGn9k", "salt": "nO"},
            "foobar12345678901": {"hash": "fgvFsy8H7ww", "salt": "9c"},
            "foobar123456789012": {"hash": "6nsIfUA4bD2", "salt": "Hi"},
            "foobar1234567890123": {"hash": "/v0NmQF2WKY", "salt": "OS"},
            "foobar12345678901234": {"hash": "Pmfg.DUC.Rs", "salt": "G3"},
            "foobar123456789012345": {"hash": "tXcQwpW/7Q.", "salt": "vV"},
            "foobar1234567890123456": {"hash": "kOOW4gLfNx6", "salt": "rv"},
            "foobar12345678901234567": {"hash": "ttw4jFym6PY", "salt": "uO"},
            "foobar123456789012345678": {"hash": "cDX1JLZATDk", "salt": "I5"},
            "foobar1234567890123456789": {
                "hash": "yvWIcShdQtE", "salt": "7t",
            },
            "foobar12345678901234567890": {
                "hash": "z7U9nEzM6eI", "salt": ".B",
            },
        }

        for username, pwd_data in testdata.items():
            u = ServiceUser.objects.create(username=username)
            u.password = 'crypt$%(salt)s$%(hash)s' % pwd_data
            u.save()

            # call twice to make sure conversion works
            self.assertTrue(u.check_password(username))
            self.assertTrue(u.check_password(username))

            # check that the hash was actually updated
            algorithm = u.password.split('$', 1)[0]
            self.assertTrue(algorithm, settings.HASH_ALGORITHM)

    @override_settings(MIN_PASSWORD_LENGTH=1)
    @override_settings(MIN_USERNAME_LENGTH=1)
    def test_apr1(self):
        testdata = {
            "f": {"hash": "wencZ6WkOMvuOANC/A8LZ0", "salt": "nErdosRy"},
            "fo": {"hash": "Vyc4Thuvc/YAbWYb1nVI70", "salt": "1aigqzQz"},
            "foo": {"hash": "cXr93EItT.sxzwewzWX4p.", "salt": "c.aI4ooC"},
            "foob": {"hash": "jN4YoWkxbtBI8D8d/Xoo3.", "salt": "wcPr1Vxv"},
            "fooba": {"hash": "Tn2C7XgOdv6v45XbC8TNn/", "salt": "nQp8UKRJ"},
            "foobar": {"hash": "XD2jiMfDOvzldmLpJl9SO.", "salt": "ilSj3Uel"},
            "foobar0": {"hash": "94YS3btM0C/5CiUvCOW.s/", "salt": "hrTvU.wk"},
            "foobar01": {
                "hash": "4Pqs5OTqXx3IGF3pm7QLv1", "salt": "EytZabM0"},
            "foobar012": {
                "hash": "eLFTYKqrZaXlLoUY6CziS/", "salt": "EkOE4ywR"},
            "foobar0123": {
                "hash": "K1k6x/RVk92AmiWnAFdEj.", "salt": "pMAaLcxe"},
            "foobar01234": {
                "hash": "PAtaCCc4kqruXb0NLoRTg0", "salt": "sAEmwZJG"},
            "foobar012345": {
                "hash": "I9pT1Vx.CMEO6wqelEAOP0", "salt": "aQ.R.N4o"},
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

        for username, pwd_data in testdata.items():
            u = ServiceUser.objects.create(username=username)
            u.password = 'apr1$%(salt)s$%(hash)s' % pwd_data
            u.save()

            self.assertTrue(u.check_password(username))
            self.assertTrue(u.check_password(username))

            # check that the hash was actually updated
            algorithm = u.password.split('$', 1)[0]
            self.assertTrue(algorithm, settings.HASH_ALGORITHM)

    @override_settings(MIN_PASSWORD_LENGTH=1)
    def test_mediawiki(self):
        testdata = {
            "user 1": {"salt": "4891a58e",
                       "hash": "222ecf008e098295058d0c9a77e19d16"},
            "user 10": {"salt": "02828b87",
                        "hash": "555f6f62e646afc840b1995d0467ef06"},
            "user 3": {"salt": "7bb9c41a",
                       "hash": "f72fbb4126a0002d88cb4afc62980d49"},
            "user 4": {"salt": "e4121fde",
                       "hash": "2de7c06ecfee2468cc0f6cf345632d29"},
            "user 5": {"salt": "99739c15",
                       "hash": "5c1ddaa0fa981ac651c6bac72f640e44"},
            "user 6": {"salt": "9650ce2d",
                       "hash": "2ad8888099fe7ce36d84c1046638f261"},
            "user 7": {"salt": "d0027595",
                       "hash": "49a25052a0690e607c1f7d103c2b51b9"},
            "user 8": {"salt": "eec0c833",
                       "hash": "971a19cefb858a481e7b0e36137774da"},
            "user 9": {"salt": "fb74cdba",
                       "hash": "9e562f64b90a6445de607f30dc745c7d"},
        }

        for username, pwd_data in testdata.items():
            u = ServiceUser.objects.create(username=username)
            u.password = 'mediawiki$%(salt)s$%(hash)s' % pwd_data
            u.save()

            password = '0123456789'[0:int(username[5:])]

            self.assertTrue(u.check_password(password))
            self.assertTrue(u.check_password(password))

            # check that the hash was actually updated
            algorithm = u.password.split('$', 1)[0]
