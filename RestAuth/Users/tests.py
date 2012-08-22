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

from RestAuth.common import errors
from RestAuth.common.testdata import *

from Users import views
from Users.models import ServiceUser, user_create, Property, user_get


class GetUsersTests(RestAuthTest):  # GET /users/
    def test_get_empty_users(self):
        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [])

    def test_get_one_user(self):
        user_create(username1, password1)

        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1])

    def test_get_two_users(self):
        user_create(username1, password1)
        user_create(username2, password1)

        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2])


class AddUserTests(RestAuthTest):  # POST /users/
    def get_usernames(self):
        return list(ServiceUser.objects.values_list('username', flat=True))

    def test_add_user(self):
        resp = self.post('/users/', {'user': username1, 'password': password1})

        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertEquals(self.get_usernames(), [username1])
        self.assertTrue(user_get(username1).check_password(password1))

    def test_add_two_users(self):
        resp = self.post('/users/', {'user': username1, 'password': password1})
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertEquals(self.get_usernames(), [username1])
        self.assertTrue(user_get(username1).check_password(password1))
        self.assertFalse(user_get(username1).check_password(password2))

        resp = self.post('/users/', {'user': username2, 'password': password2})
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertEquals(self.get_usernames(), [username1, username2])

        self.assertTrue(user_get(username1).check_password(password1))
        self.assertFalse(user_get(username1).check_password(password2))
        self.assertTrue(user_get(username2).check_password(password2))
        self.assertFalse(user_get(username2).check_password(password1))

    def test_add_user_twice(self):
        self.assertEquals(self.get_usernames(), [])
        resp = self.post('/users/', {'user': username1, 'password': password1})
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertEquals(self.get_usernames(), [username1])

        self.assertTrue(user_get(username1).check_password(password1))
        self.assertFalse(user_get(username1).check_password(password2))

        # add again:
        resp = self.post('/users/', {'user': username1, 'password': password2})
        self.assertEquals(resp.status_code, httplib.CONFLICT)
        self.assertEquals(self.get_usernames(), [username1])

        # check that we still have the old password:
        self.assertTrue(user_get(username1).check_password(password1))
        self.assertFalse(user_get(username1).check_password(password2))

    def test_add_user_no_pass(self):
        resp = self.post('/users/', {'user': username1})
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertEquals(self.get_usernames(), [username1])
        user = user_get(username1)
        self.assertFalse(user.check_password(''))
        self.assertFalse(user.check_password(None))
        self.assertFalse(user.check_password(password1))
        self.assertFalse(user.check_password(password2))

        resp = self.post('/users/', {'user': username2, 'password': ''})
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertEquals(self.get_usernames(), [username1, username2])
        user = user_get(username2)
        self.assertFalse(user.check_password(''))
        self.assertFalse(user.check_password(None))
        self.assertFalse(user.check_password(password1))
        self.assertFalse(user.check_password(password2))

        resp = self.post('/users/', {'user': username3, 'password': None})
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertEquals(
            self.get_usernames(), [username1, username2, username3])
        user = user_get(username3)
        self.assertFalse(user.check_password(''))
        self.assertFalse(user.check_password(None))
        self.assertFalse(user.check_password(password1))
        self.assertFalse(user.check_password(password2))

    def test_add_user_with_property(self):
        resp = self.post('/users/', {'user': username1, 'properties': {
            propkey1: propval1
        }})

        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertEquals(self.get_usernames(), [username1])

        user = user_get(username1)
        self.assertDictEqual({propkey1: propval1}, user.get_properties())

    def test_add_user_with_properties(self):
        props = {propkey1: propval1, propkey2: propval2}
        resp = self.post('/users/', {'user': username1, 'properties': props})
        self.assertEquals(resp.status_code, httplib.CREATED)

        user = user_get(username1)
        self.assertDictEqual(props, user.get_properties())

    def test_bad_requests(self):
        self.assertEquals(self.get_usernames(), [])

        resp = self.post('/users/', {'password': 'foobar'})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertEquals(self.get_usernames(), [])

        resp = self.post('/users/', {})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertEquals(self.get_usernames(), [])

        resp = self.post('/users/', {
            'userasdf': username1, 'passwordasdf': 'foobar'
        })
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertEquals(self.get_usernames(), [])

    def test_add_invalid_username(self):
        username = 'foo/bar'
        resp = self.post('/users/', {'user': username, 'password': password1})
        self.assertEquals(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertEquals(self.get_usernames(), [])

        username = 'foo:bar'
        resp = self.post('/users/', {'user': username, 'password': password1})
        self.assertEquals(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertEquals(self.get_usernames(), [])

    def test_add_user_with_long_username(self):
        username = 'abc' * 200
        resp = self.post('/users/', {'user': username})
        self.assertEquals(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertEquals(self.get_usernames(), [])


class UserTests(RestAuthTest):
    def setUp(self):
        RestAuthTest.setUp(self)

        # two users, so we can make sure nothing leaks to the other user
        self.user1 = user_create(username1, password1)
        self.user2 = user_create(username2, password2)


class UserExistsTests(UserTests):  # GET /users/<user>/
    def test_user_exists(self):
        resp = self.get('/users/%s/' % username1)
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        resp = self.get('/users/%s/' % username2)
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        resp = self.get('/users/%s/' % username3)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')


class VerifyPasswordsTest(UserTests):  # POST /users/<user>/
    def test_user_doesnt_exist(self):
        resp = self.post('/users/%s/' % username3, {'password': 'foobar'})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_verify_password(self):
        resp = self.post('/users/%s/' % username1, {'password': password1})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        resp = self.post('/users/%s/' % username2, {'password': password2})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

    def test_verify_wrong_password(self):
        resp = self.post('/users/%s/' % username1, {'password': 'wrong'})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

        resp = self.post('/users/%s/' % username2, {'password': 'wrong'})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_verify_disabled_password(self):
        user3 = user_create(username3, None)
        user4 = user_create(username4, '')

        resp = self.post('/users/%s/' % username3, {'password': 'wrong'})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')
        resp = self.post('/users/%s/' % username3, {'password': ''})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')
        resp = self.post('/users/%s/' % username3, {'password': None})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

        resp = self.post('/users/%s/' % username4, {'password': 'wrong'})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')
        resp = self.post('/users/%s/' % username4, {'password': ''})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')
        resp = self.post('/users/%s/' % username4, {'password': None})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_bad_requests(self):
        resp = self.post('/users/%s/' % username1, {})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)

        resp = self.post('/users/%s/' % username1, {'foo': 'bar'})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)

        resp = self.post('/users/%s/' % username1,
                         {'password': 'foobar', 'foo': 'bar'})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)


class ChangePasswordsTest(UserTests):  # PUT /users/<user>/
    def test_user_doesnt_exist(self):
        resp = self.put('/users/%s/' % username3, {'password': password3})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEquals(resp['Resource-Type'], 'user')

    def test_change_password(self):
        resp = self.put('/users/%s/' % username1, {'password': password3})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertFalse(user_get(username1).check_password(password1))
        self.assertFalse(user_get(username1).check_password(password2))
        self.assertTrue(user_get(username1).check_password(password3))

        # check user2, just to be sure:
        self.assertFalse(user_get(username2).check_password(password1))
        self.assertTrue(user_get(username2).check_password(password2))
        self.assertFalse(user_get(username2).check_password(password3))

    def test_disable_password(self):
        resp = self.put('/users/%s/' % username1, {})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertFalse(user_get(username1).check_password(password1))
        self.assertFalse(user_get(username1).check_password(''))
        self.assertFalse(user_get(username1).check_password(None))

        resp = self.put('/users/%s/' % username1, {'password': ''})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertFalse(user_get(username1).check_password(password1))
        self.assertFalse(user_get(username1).check_password(''))
        self.assertFalse(user_get(username1).check_password(None))

        resp = self.put('/users/%s/' % username1, {'password': None})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertFalse(user_get(username1).check_password(password1))
        self.assertFalse(user_get(username1).check_password(''))
        self.assertFalse(user_get(username1).check_password(None))

    def test_bad_requests(self):
        resp = self.put('/users/%s/' % username1, {'foo': password2})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertTrue(user_get(username1).check_password(password1))

        resp = self.put('/users/%s/' % username1,
                        {'password': password3, 'foo': 'bar'})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertTrue(user_get(username1).check_password(password1))


class DeleteUserTest(UserTests):  # DELETE /users/<user>/
    def test_user_doesnt_exist(self):
        resp = self.delete('/users/%s/' % username3)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_delete_user(self):
        resp = self.delete('/users/%s/' % username1)
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertFalse(
            ServiceUser.objects.filter(username=username1).exists())
        self.assertTrue(
            ServiceUser.objects.filter(username=username2).exists())


class PropertyTests(RestAuthTest):
    """
    Superclass for tests on
    ``/users/<user>/props/`` and ``/users/<user>/props/<prop>/``.
    """
    def setUp(self):
        RestAuthTest.setUp(self)

        # two users, so we can make sure nothing leaks to the other user
        self.user1 = user_create(username1, password1)
        self.user2 = user_create(username2, password2)


class GetAllPropertiesTests(PropertyTests):  # GET /users/<user>/props/
    def test_user_doesnot_exist(self):
        resp = self.get('/users/%s/props/' % username3)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_get_no_properties(self):
        resp = self.get('/users/%s/props/' % username1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

    def test_get_single_property(self):
        self.user1.add_property(propkey1, propval1)

        resp = self.get('/users/%s/props/' % username1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {propkey1: propval1})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

    def test_get_two_properties(self):
        self.user1.add_property(propkey1, propval1)
        self.user1.add_property(propkey2, propval2)

        resp = self.get('/users/%s/props/' % username1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'),
                             {propkey1: propval1, propkey2: propval2})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {})

    def test_get_multiple_properties(self):
        self.user1.add_property(propkey1, propval1)
        self.user1.add_property(propkey2, propval2)
        self.user2.add_property(propkey3, propval3)

        resp = self.get('/users/%s/props/' % username1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'),
                             {propkey1: propval1, propkey2: propval2})

        resp = self.get('/users/%s/props/' % username2)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertDictEqual(self.parse(resp, 'dict'), {propkey3: propval3})


class CreatePropertyTests(PropertyTests):  # POST /users/<user>/props/
    def test_user_doesnt_exist(self):
        resp = self.post('/users/%s/props/' % username3,
                         {'prop': propkey1, 'value': propval1})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

        # check that no properties were added to the database:
        self.assertEquals(list(Property.objects.all()), [])

    def test_create_property(self):
        resp = self.post('/users/%s/props/' % username1,
                         {'prop': propkey1, 'value': propval1})
        self.assertEquals(resp.status_code, httplib.CREATED)

        self.assertDictEqual(self.user1.get_properties(), {propkey1: propval1})
        self.assertDictEqual(self.user2.get_properties(), {})

        # we create a second property
        resp = self.post('/users/%s/props/' % username1,
                         {'prop': propkey2, 'value': propval2})
        self.assertEquals(resp.status_code, httplib.CREATED)

        self.assertDictEqual(self.user1.get_properties(),
                             {propkey1: propval1, propkey2: propval2})
        self.assertDictEqual(self.user2.get_properties(), {})

        # and a property for second user:
        resp = self.post('/users/%s/props/' % username2,
                         {'prop': propkey3, 'value': propval3})
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertDictEqual(self.user1.get_properties(),
                             {propkey1: propval1, propkey2: propval2})
        self.assertDictEqual(self.user2.get_properties(), {propkey3: propval3})

    def test_create_existing_property(self):
        self.user1.add_property(propkey1, propval1)

        resp = self.post('/users/%s/props/' % username1,
                         {'prop': propkey1, 'value': propval2})
        self.assertEquals(resp.status_code, httplib.CONFLICT)

        self.assertDictEqual(self.user1.get_properties(), {propkey1: propval1})
        self.assertDictEqual(self.user2.get_properties(), {})

    def test_create_invalid_property(self):
        resp = self.post('/users/%s/props/' % username1,
                         {'prop': "foo:bar", 'value': propval2})
        self.assertEquals(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertDictEqual(self.user1.get_properties(), {})

    def test_bad_requests(self):
        resp = self.post('/users/%s/props/' % username2, {})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertDictEqual(self.user1.get_properties(), {})
        self.assertDictEqual(self.user2.get_properties(), {})

        resp = self.post('/users/%s/props/' % username2, {'foo': 'bar'})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertDictEqual(self.user1.get_properties(), {})
        self.assertDictEqual(self.user2.get_properties(), {})

        resp = self.post('/users/%s/props/' % username2, {
            'foo': 'bar', 'prop': propkey3, 'value': propval3
        })
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertDictEqual(self.user1.get_properties(), {})
        self.assertDictEqual(self.user2.get_properties(), {})


class SetMultiplePropertiesTests(PropertyTests):
    def test_user_doesnt_exist(self):
        resp = self.put('/users/%s/props/' % username3,
                        {propkey1: propval1, propkey2: propval2})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_no_property(self):
        resp = self.put('/users/%s/props/' % username1, {})
        self.assertDictEqual(self.user1.get_properties(), {})

    def test_create_one_property(self):
        testdict = {propkey1: propval1}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

    def test_create_two_properties(self):
        testdict = {propkey1: propval1, propkey2: propval2}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

    def test_create_three_properties(self):
        testdict = {propkey1: propval1, propkey2: propval2, propkey3: propval3}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

    def test_set_one_property(self):
        testdict = {propkey1: propval1}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

        testdict = {propkey1: propval2}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

    def test_set_two_properties(self):
        testdict = {propkey1: propval1, propkey2: propval2}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

        testdict = {propkey1: propval3, propkey2: propval4}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

    def test_set_three_properties(self):
        testdict = {propkey1: propval1, propkey2: propval2, propkey3: propval3}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

        testdict = {propkey1: propval2, propkey2: propval5, propkey3: propval4}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

    def test_mix_set_and_create(self):
        testdict = {propkey1: propval1}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)

        testdict = {propkey1: propval1, propkey2: propval2}
        resp = self.put('/users/%s/props/' % username1, testdict)
        self.assertDictEqual(self.user1.get_properties(), testdict)


class GetPropertyTests(PropertyTests):  # GET /users/<user>/props/<prop>/
    def test_user_doesnt_exist(self):
        resp = self.get('/users/%s/props/%s/' % (username3, propkey1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_property_doesnt_exist(self):
        resp = self.get('/users/%s/props/%s/' % (username1, propkey1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'property')

    def test_get_property(self):
        self.user1.add_property(propkey1, propval1)

        resp = self.get('/users/%s/props/%s/' % (username1, propkey1))
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'str'), propval1)

        # check that user2 doesn't have it:
        resp = self.get('/users/%s/props/%s/' % (username2, propkey1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'property')


class SetPropertyTests(PropertyTests):  # PUT /users/<user>/props/<prop>/
    def test_user_doesnt_exist(self):
        resp = self.put(
            '/users/%s/props/%s/' % (username3, propkey1), {'value': propval1})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

        # assert that no property has been created:
        self.assertEquals(list(Property.objects.all()), [])

    def test_set_new_property(self):
        # set a property
        resp = self.put(
            '/users/%s/props/%s/' % (username1, propkey1), {'value': propval1})
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertEquals(
            user_get(username1).property_set.get(key=propkey1).value, propval1)
        self.assertFalse(
            user_get(username2).property_set.filter(key=propkey1).exists())

    def test_set_existing_property(self):
        self.user1.add_property(propkey1, propval1)

        # set a property again and assert that it returns the old value:
        resp = self.put(
            '/users/%s/props/%s/' % (username1, propkey1), {'value': propval2})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'str'), propval1)
        self.assertEquals(
            user_get(username1).property_set.get(key=propkey1).value, propval2)
        self.assertFalse(
            user_get(username2).property_set.filter(key=propkey1).exists())

    def test_bad_request(self):
        # do some bad request tests:
        resp = self.put('/users/%s/props/%s/' % (username1, propkey1), {})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertEquals(
            list(Property.objects.all().values_list('key', 'value')), [])

        resp = self.put('/users/%s/props/%s/' % (username1, propkey1),
                        {'foo': 'bar'})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertEquals(
            list(Property.objects.all().values_list('key', 'value')), [])

        resp = self.put('/users/%s/props/%s/' % (username1, propkey1),
                        {'value': propkey3, 'foo': 'bar'})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertEquals(
            list(Property.objects.all().values_list('key', 'value')), [])


class DeletePropertyTests(PropertyTests):  # DELETE /users/<user>/props/<prop>/
    def test_user_doesnt_exist(self):
        resp = self.delete('/users/%s/props/%s/' % (username3, propkey1),)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_property_doesnt_exist(self):
        resp = self.delete('/users/%s/props/%s/' % (username1, propkey1),)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'property')

    def test_delete_property(self):
        self.user1.add_property(propkey1, propval1)
        self.user1.add_property(propkey2, propval2)

        resp = self.delete('/users/%s/props/%s/' % (username1, propkey1),)
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertItemsEqual(
            self.user1.property_set.values_list('key', 'value').all(),
            [(propkey2, propval2)]
        )

    def test_cross_user(self):
        # two users have properties with the same key, we verify that deleting
        # one doesn't delete the other:
        self.user1.add_property(propkey1, propval1)
        self.user2.add_property(propkey1, propval1)

        resp = self.delete('/users/%s/props/%s/' % (username1, propkey1),)
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertItemsEqual(list(self.user1.property_set.all()), [])
        self.assertItemsEqual(
            self.user2.property_set.values_list('key', 'value').all(),
            [(propkey1, propval1)]
        )


class HashTest(RestAuthTest):
    def test_crypt(self):
        """
        .. todo:: Django 1.4: enable one and two-letter test cases and set
           MIN_USERNAME_LENGTH to 1. see:
           https://docs.djangoproject.com/en/dev/topics/testing/#overriding-settings
        """

        testdata = {
            #"f": {
            #    "password": {
            #        "hash": "zByHy85N5JE", "salt": "LG", "algorithm": "crypt"
            #    }
            #},
            #"fo": {
            #    "password": {
            #        "hash": "Lb4p57NVOh6", "salt": "qO", "algorithm": "crypt"
            #    }
            #},
            "foo": {
                "password": {
                    "hash": "SOM3CYj26Xk", "salt": "L/", "algorithm": "crypt"
                }
            },
            "foob": {
                "password": {
                    "hash": "6J6SsDmmvPE", "salt": "fq", "algorithm": "crypt"
                }
            },
            "fooba": {
                "password": {
                    "hash": "45YY/lBbQL.", "salt": "EG", "algorithm": "crypt"
                }
            },
            "foobar": {
                "password": {
                    "hash": "5RKNB0QSl4g", "salt": "wC", "algorithm": "crypt"
                }
            },
            "foobar1": {
                "password": {
                    "hash": "3.K3kCyb2AA", "salt": "st", "algorithm": "crypt"
                }
            },
            "foobar12": {
                "password": {
                    "hash": "LbMAd.nZIv2", "salt": "ca", "algorithm": "crypt"
                }
            },
            "foobar123": {
                "password": {
                    "hash": "9yA..KnYzIk", "salt": "s0", "algorithm": "crypt"
                }
            },
            "foobar1234": {
                "password": {
                    "hash": "FOG2CHhzJm.", "salt": "SF", "algorithm": "crypt"
                }
            },
            "foobar12345": {"password": {
                "hash": "uqrrlepaCqE", "salt": "vB", "algorithm": "crypt"}},
            "foobar123456": {
                "password": {
                    "hash": "44fvIAOpK5U", "salt": "ep", "algorithm": "crypt"
                }
            },
            "foobar1234567": {
                "password": {
                    "hash": "TWg6AU5FFN6", "salt": "T.", "algorithm": "crypt"
                }
            },
            "foobar12345678": {
                "password": {
                    "hash": "KbFo0bhBYRs", "salt": "FF", "algorithm": "crypt"
                }
            },
            "foobar123456789": {
                "password": {
                    "hash": "exX507cNB0.", "salt": "TU", "algorithm": "crypt"
                }
            },
            "foobar1234567890": {
                "password": {
                    "hash": "FITBq2CGn9k", "salt": "nO", "algorithm": "crypt"
                }
            },
            "foobar12345678901": {
                "password": {
                    "hash": "fgvFsy8H7ww", "salt": "9c", "algorithm": "crypt"
                }
            },
            "foobar123456789012": {
                "password": {
                    "hash": "6nsIfUA4bD2", "salt": "Hi", "algorithm": "crypt"
                }
            },
            "foobar1234567890123": {
                "password": {
                    "hash": "/v0NmQF2WKY", "salt": "OS", "algorithm": "crypt"
                }
            },
            "foobar12345678901234": {
                "password": {
                    "hash": "Pmfg.DUC.Rs", "salt": "G3", "algorithm": "crypt"
                }
            },
            "foobar123456789012345": {
                "password": {
                    "hash": "tXcQwpW/7Q.", "salt": "vV", "algorithm": "crypt"
                }
            },
            "foobar1234567890123456": {
                "password": {
                    "hash": "kOOW4gLfNx6", "salt": "rv", "algorithm": "crypt"
                }
            },
            "foobar12345678901234567": {
                "password": {
                    "hash": "ttw4jFym6PY", "salt": "uO", "algorithm": "crypt"
                }
            },
            "foobar123456789012345678": {
                "password": {
                    "hash": "cDX1JLZATDk", "salt": "I5", "algorithm": "crypt"
                }
            },
            "foobar1234567890123456789": {
                "password": {
                    "hash": "yvWIcShdQtE", "salt": "7t", "algorithm": "crypt"
                }
            },
            "foobar12345678901234567890": {
                "password": {
                    "hash": "z7U9nEzM6eI", "salt": ".B", "algorithm": "crypt"
                }
            },
        }

        for username, pwd_data in testdata.items():
            u = ServiceUser.objects.create(username=username)
            u.algorithm = pwd_data['password']['algorithm']
            u.salt = pwd_data['password']['salt']
            u.hash = pwd_data['password']['hash']
            u.save()

            self.assertTrue(u.check_password(username))

            u.delete()

    def test_apr1(self):
        """
        .. todo:: Django 1.4: enable one and two-letter test cases and set
           MIN_USERNAME_LENGTH to 1. see:
           https://docs.djangoproject.com/en/dev/topics/testing/#overriding-settings
        """

        testdata = {
            #"f": {"hash": "wencZ6WkOMvuOANC/A8LZ0", "salt": "nErdosRy",
            #      "algorithm": "apr1"},
            #"fo": {"hash": "Vyc4Thuvc/YAbWYb1nVI70", "salt": "1aigqzQz",
            #       "algorithm": "apr1"},
            "foo": {"hash": "cXr93EItT.sxzwewzWX4p.", "salt": "c.aI4ooC",
                    "algorithm": "apr1"},
            "foob": {"hash": "jN4YoWkxbtBI8D8d/Xoo3.", "salt": "wcPr1Vxv",
                     "algorithm": "apr1"},
            "fooba": {"hash": "Tn2C7XgOdv6v45XbC8TNn/", "salt": "nQp8UKRJ",
                      "algorithm": "apr1"},
            "foobar": {"hash": "XD2jiMfDOvzldmLpJl9SO.", "salt": "ilSj3Uel",
                       "algorithm": "apr1"},
            "foobar0": {"hash": "94YS3btM0C/5CiUvCOW.s/", "salt": "hrTvU.wk",
                        "algorithm": "apr1"},
            "foobar01": {"hash": "4Pqs5OTqXx3IGF3pm7QLv1", "salt": "EytZabM0",
                         "algorithm": "apr1"},
            "foobar012": {"hash": "eLFTYKqrZaXlLoUY6CziS/", "salt": "EkOE4ywR",
                          "algorithm": "apr1"},
            "foobar0123": {"hash": "K1k6x/RVk92AmiWnAFdEj.",
                           "salt": "pMAaLcxe", "algorithm": "apr1"},
            "foobar01234": {"hash": "PAtaCCc4kqruXb0NLoRTg0",
                            "salt": "sAEmwZJG", "algorithm": "apr1"},
            "foobar012345": {"hash": "I9pT1Vx.CMEO6wqelEAOP0",
                             "salt": "aQ.R.N4o", "algorithm": "apr1"},
            "foobar0123456": {"hash": "G4zjuqUYGU6nFSxPFyO4x0",
                              "salt": "HvbXrlI/", "algorithm": "apr1"},
            "foobar01234567": {"hash": "cVAXAQ42OPeHSC3SNSOHS/",
                               "salt": "TDF/0tAf", "algorithm": "apr1"},
            "foobar012345678": {"hash": "HASHq302/S19PI.RLbb400",
                                "salt": "zaKZEcLq", "algorithm": "apr1"},
            "foobar0123456789": {"hash": "TzOmxdrHqe0HfwxIPXlU10",
                                 "salt": "NjALUYrK", "algorithm": "apr1"},
            "foobar01234567890": {"hash": "aQ127rgKtHR098iUEgW.F1",
                                  "salt": "SJJuaEKa", "algorithm": "apr1"},
            "foobar012345678901": {"hash": "TLkfRBIjGqjL4clR0873c1",
                                   "salt": "hDJaX1Sa", "algorithm": "apr1"},
            "foobar0123456789012": {"hash": "1OIrHIzF.HOQ72wbcFWzU0",
                                    "salt": "HlBLH.DU", "algorithm": "apr1"},
            "foobar01234567890123": {"hash": "hnBripG.5yMPXE4FJg7Np0",
                                     "salt": "snk9PtYt", "algorithm": "apr1"},
            "foobar012345678901234": {
                "hash": "zbRB1BrZmWaFKJMqKyTum0", "salt": "NyCJRWye",
                "algorithm": "apr1"
            },
            "foobar0123456789012345": {
                "hash": "UugUUu7D7pABxWg2p2ovc1", "salt": "c3tj3eYu",
                "algorithm": "apr1"
            },
            "foobar01234567890123456": {
                "hash": "8iXmJONIozEPLup/2KgQp/", "salt": "tecrND8A",
                "algorithm": "apr1"
            },
            "foobar012345678901234567": {
                "hash": "fx2Tly.fIvybOKAbtUWMN/", "salt": "JpSOF7qJ",
                "algorithm": "apr1"
            },
            "foobar0123456789012345678": {
                "hash": "fGBumUrVrJ40UB/Q2K1lI.", "salt": "fS58gR6t",
                "algorithm": "apr1"
            },
            "foobar01234567890123456789": {
                "hash": "bEsAOMdUIs1GNh5LLjlP1.", "salt": "PLG28sJA",
                "algorithm": "apr1"
            },
            "foobar012345678901234567890": {
                "hash": "CmoV8ccWcCEzBV01Pq496/", "salt": "MM49C.Vs",
                "algorithm": "apr1"
            },
            "foobar0123456789012345678901": {
                "hash": "2tGWA3NHFeGAEmSXZhYnR/", "salt": "9n8nToVo",
                "algorithm": "apr1"
            },
            "foobar01234567890123456789012": {
                "hash": "1cyFn3QVsTQf5RID7O6wC.", "salt": "88x7/ARO",
                "algorithm": "apr1"
            },
            "foobar012345678901234567890123": {
                "hash": "ADOeE2pC3SIrRPpj1wdJs/", "salt": "r/oMeWiA",
                "algorithm": "apr1"
            },
            "foobar0123456789012345678901234": {
                "hash": "O6pOM0l0DEfJipuhQLk1u/", "salt": "hViGYCEr",
                "algorithm": "apr1"
            },
            "foobar01234567890123456789012345": {
                "hash": "WcPoFDPY2hMpalN2bZibX.", "salt": "2QBHE4/Q",
                "algorithm": "apr1"
            },
            "foobar012345678901234567890123456": {
                "hash": "BHCTbYz7NZZK4HAFuHLzG.", "salt": "knaM/8D4",
                "algorithm": "apr1"
            },
            "foobar0123456789012345678901234567": {
                "hash": "QyzsGHXVFAEu1aO9rkphD0", "salt": "gfdWhcS7",
                "algorithm": "apr1"
            },
            "foobar01234567890123456789012345678": {
                "hash": "Frfmzydl8OC7RrMbkTUY21", "salt": "v8oc0omI",
                "algorithm": "apr1"
            },
            "foobar012345678901234567890123456789": {
                "hash": "ZvOpfsrYFSUgUwtVsCUBR0", "salt": "GAAPD33a",
                "algorithm": "apr1"
            },
            "foobar0123456789012345678901234567890": {
                "hash": "D2ISHi8yEIL/0MzNWiDis.", "salt": "3Glrt6Oh",
                "algorithm": "apr1"
            },
        }

        for username, pwd_data in testdata.items():
            u = ServiceUser.objects.create(username=username)
            u.algorithm = pwd_data['algorithm']
            u.salt = pwd_data['salt']
            u.hash = pwd_data['hash']
            u.save()

            self.assertTrue(u.check_password(username))

            u.delete()

    def test_mediawiki(self):
        testdata = {
            "user 1": {"algorithm": "mediawiki", "salt": "4891a58e",
                       "hash": "222ecf008e098295058d0c9a77e19d16"},
            "user 10": {"algorithm": "mediawiki", "salt": "02828b87",
                        "hash": "555f6f62e646afc840b1995d0467ef06"},
            "user 3": {"algorithm": "mediawiki", "salt": "7bb9c41a",
                       "hash": "f72fbb4126a0002d88cb4afc62980d49"},
            "user 4": {"algorithm": "mediawiki", "salt": "e4121fde",
                       "hash": "2de7c06ecfee2468cc0f6cf345632d29"},
            "user 5": {"algorithm": "mediawiki", "salt": "99739c15",
                       "hash": "5c1ddaa0fa981ac651c6bac72f640e44"},
            "user 6": {"algorithm": "mediawiki", "salt": "9650ce2d",
                       "hash": "2ad8888099fe7ce36d84c1046638f261"},
            "user 7": {"algorithm": "mediawiki", "salt": "d0027595",
                       "hash": "49a25052a0690e607c1f7d103c2b51b9"},
            "user 8": {"algorithm": "mediawiki", "salt": "eec0c833",
                       "hash": "971a19cefb858a481e7b0e36137774da"},
            "user 9": {"algorithm": "mediawiki", "salt": "fb74cdba",
                       "hash": "9e562f64b90a6445de607f30dc745c7d"},
        }

        for username, pwd_data in testdata.items():
            u = ServiceUser.objects.create(username=username)
            u.algorithm = pwd_data['algorithm']
            u.salt = pwd_data['salt']
            u.hash = pwd_data['hash']
            u.save()

            password = '0123456789'[0:int(username[5:])]

            self.assertTrue(u.check_password(password))

            u.delete()
