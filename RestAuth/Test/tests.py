# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from django.utils.six.moves import http_client

from common.testdata import groupname1
from common.testdata import group_backend
from common.testdata import password1
from common.testdata import propkey1
from common.testdata import propval1
from common.testdata import propval2
from common.testdata import property_backend
from common.testdata import RestAuthTransactionTest
from common.testdata import user_backend
from common.testdata import username1


class CreateUserTest(RestAuthTransactionTest):
    def test_dry_run_create_user(self):
        resp = self.post('/test/users/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.CREATED)
        self.assertEqual(list(user_backend.list()), [])

    def test_dry_run_create_user_with_pass(self):
        resp = self.post('/test/users/', {'user': username1, 'password': password1})
        self.assertEqual(resp.status_code, http_client.CREATED)
        self.assertEqual(list(user_backend.list()), [])

    def test_dry_run_create_user_with_props(self):
        resp = self.post('/test/users/', {'user': username1, 'properties': {'foo': 'bar'}})
        self.assertEqual(resp.status_code, http_client.CREATED)
        self.assertEqual(list(user_backend.list()), [])

    def test_dry_run_create_user_with_pass_and_props(self):
        content = {'user': username1, 'password': password1, 'properties': {'foo': 'bar'}}
        resp = self.post('/test/users/', content)
        self.assertEqual(resp.status_code, http_client.CREATED)
        self.assertEqual(list(user_backend.list()), [])

    def test_dry_run_create_existing_user(self):
        user = self.create_user(username=username1)
        self.assertItemsEqual([user.username], list(user_backend.list()))

        resp = self.post('/test/users/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.CONFLICT)
        self.assertItemsEqual([user.username], list(user_backend.list()))

    def test_dry_run_create_invalid_user(self):
        resp = self.post('/test/users/', {'user': 'foo/bar'})
        self.assertEqual(resp.status_code, http_client.PRECONDITION_FAILED)
        self.assertEqual(list(user_backend.list()), [])

    def test_dry_run_create_short_user(self):
        resp = self.post('/test/users/', {'user': 'x'})
        self.assertEqual(resp.status_code, http_client.PRECONDITION_FAILED)
        self.assertEqual(list(user_backend.list()), [])

    def test_create_with_too_short_pass(self):
        resp = self.post('/test/users/', {'user': username1, 'password': 'a'})
        self.assertEqual(resp.status_code, http_client.PRECONDITION_FAILED)
        self.assertEqual(list(user_backend.list()), [])


class CreatePropertyTest(RestAuthTransactionTest):
    def setUp(self):
        RestAuthTransactionTest.setUp(self)
        self.user = self.create_user(username=username1)

    def tearDown(self):
        super(CreatePropertyTest, self).tearDown()
        property_backend.testTearDown()

    def test_create_property(self):
        url = '/test/users/%s/props/' % self.user.username
        resp = self.post(url, {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, http_client.CREATED)

        self.assertProperties(self.user, {})

    def test_create_existing_property(self):
        property_backend.create(self.user, propkey1, propval1)

        url = '/test/users/%s/props/' % self.user.username
        resp = self.post(url, {'prop': propkey1, 'value': propval2})
        self.assertEqual(resp.status_code, http_client.CONFLICT)

        self.assertProperties(self.user, {propkey1: propval1})

    def test_create_invalid_property(self):
        url = '/test/users/%s/props/' % self.user.username
        resp = self.post(url, {'prop': 'foo/bar', 'value': propval1})
        self.assertEqual(resp.status_code, http_client.PRECONDITION_FAILED)
        self.assertProperties(self.user, {})

        resp = self.post(url, {'prop': 'foo:bar', 'value': propval1})
        self.assertEqual(resp.status_code, http_client.PRECONDITION_FAILED)
        self.assertProperties(self.user, {})

    def test_create_property_for_non_existing_user(self):
        url = '/test/users/%s/props/' % 'wronguser'
        resp = self.post(url, {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)

        self.assertProperties(self.user, {})

    def test_create_property_for_invalid_user(self):
        url = '/test/users/%s/props/' % 'wrong\\user'
        resp = self.post(url, {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertProperties(self.user, {})


class CreateGroupTest(RestAuthTransactionTest):
    def test_dry_run_create_group(self):
        resp = self.post('/test/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.CREATED)
        self.assertFalse(group_backend.list(self.service))

    def test_dry_run_create_existing_group(self):
        group = group_backend.create(service=self.service, name=groupname1)

        resp = self.post('/test/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.CONFLICT)
        self.assertItemsEqual([group.name], group_backend.list(self.service))

    def test_dry_run_create_invalid_group(self):
        resp = self.post('/test/groups/', {'group': 'foo/bar'})
        self.assertEqual(resp.status_code, http_client.PRECONDITION_FAILED)
        self.assertFalse(group_backend.list(self.service))
