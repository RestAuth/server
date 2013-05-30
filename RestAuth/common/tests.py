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

from django.core.exceptions import ImproperlyConfigured
from django.test.client import Client
from django.test.client import RequestFactory
from django.utils.unittest import TestCase

from django.utils.six.moves import http_client

from RestAuthCommon import handlers

from RestAuth.Services.models import Service
from RestAuth.Users.validators import Validator
from RestAuth.Users.validators import get_validators
from RestAuth.Users.validators import load_username_validators
from RestAuth.Users.validators import validate_username
from RestAuth.backends.base import GroupInstance
from RestAuth.backends.base import UserInstance
from RestAuth.common.errors import UsernameInvalid
from RestAuth.common.middleware import RestAuthMiddleware
from RestAuth.common.testdata import RestAuthTest
from RestAuth.common.testdata import user_backend
from RestAuth.common.testdata import username1
from RestAuth.common.utils import import_path


class RestAuthMiddlewareTests(TestCase):
    def setUp(self):
        self.handler = handlers.json()
        self.extra = {
            'HTTP_ACCEPT': self.handler.mime,
            'REMOTE_USER': 'vowi',
            'content_type': self.handler.mime,
        }

        self.factory = RequestFactory()
        self.mw = RestAuthMiddleware()

    def tearDown(self):
        Service.objects.all().delete()

    def test_post_missing_content_type(self):
        content = self.handler.marshal_dict({'user': username1})
        request = self.factory.post('/users/', content, **self.extra)
        del request.META['CONTENT_TYPE']
        resp = self.mw.process_request(request)
        self.assertEqual(resp.status_code, http_client.UNSUPPORTED_MEDIA_TYPE)

    def test_put_missing_content_type(self):
        content = self.handler.marshal_dict({'user': username1})
        request = self.factory.put('/users/', content, **self.extra)
        del request.META['CONTENT_TYPE']
        resp = self.mw.process_request(request)
        self.assertEqual(resp.status_code, http_client.UNSUPPORTED_MEDIA_TYPE)


class ContentTypeTests(RestAuthTest):
    def setUp(self):
        RestAuthTest.setUp(self)
        self.factory = RequestFactory()

    def test_wrong_content_type_header(self):
        content = self.handler.marshal_dict({'user': username1})
        extra = self.extra
        del extra['content_type']
        resp = self.c.post('/users/', content, content_type='foo/bar', **extra)
        self.assertEqual(resp.status_code, http_client.UNSUPPORTED_MEDIA_TYPE)
        self.assertItemsEqual(user_backend.list(), [])

    def test_wrong_accept_header(self):
        extra = self.extra
        extra['HTTP_ACCEPT'] = 'foo/bar'
        resp = self.c.get('/users/', **extra)
        self.assertEqual(resp.status_code, http_client.NOT_ACCEPTABLE)
        self.assertItemsEqual(user_backend.list(), [])

    def test_wrong_content(self):
        content = 'no_json_at_all}}}'
        resp = self.c.post('/users/', content, **self.extra)
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)
        self.assertItemsEqual(user_backend.list(), [])

validators = (
    'RestAuth.Users.validators.EmailValidator',
    'RestAuth.Users.validators.MediaWikiValidator',
    'RestAuth.Users.validators.LinuxValidator',
    'RestAuth.Users.validators.WindowsValidator',
    'RestAuth.Users.validators.XMPPValidator',
)


class ValidatorTests(RestAuthTest):
    def setUp(self):
        super(ValidatorTests, self).setUp()
        load_username_validators(validators)

    def tearDown(self):
        super(ValidatorTests, self).tearDown()
        load_username_validators()

    def test_illegal_chars(self):
        self.assertRaises(UsernameInvalid, validate_username, 'foo>bar')

    def test_reserved_username(self):
        self.assertRaises(UsernameInvalid, validate_username,
                          'mediawiki default')

    def test_force_ascii(self):
        self.assertRaises(UsernameInvalid, validate_username, username1)

    def test_no_whitespace(self):
        self.assertRaises(UsernameInvalid, validate_username, 'foo bar')

    def assert_validators(self, validators, substract=0):
        load_username_validators(validators)

        new_validators = get_validators()
        self.assertEqual(len(validators) - substract, len(new_validators))
        for val in new_validators:
            self.assertTrue(isinstance(val, Validator), type(val))

    def test_loading(self):
        self.assert_validators((
            'RestAuth.Users.validators.MediaWikiValidator',
        ))

        # substract 1 because one validator has no 'check' method:
        self.assert_validators((
            'RestAuth.Users.validators.EmailValidator',
            'RestAuth.Users.validators.MediaWikiValidator',
            'RestAuth.Users.validators.XMPPValidator',  # no check method!
        ), substract=1)


class ImportTests(RestAuthTest):
    def test_malformed_path(self):
        self.assertRaises(ImproperlyConfigured, import_path, 'foobar')

    def test_unknown_path(self):
        self.assertRaises(ImproperlyConfigured, import_path,
                          'Unknown.Module')

    def test_unkown_class(self):
        self.assertRaises(ImproperlyConfigured, import_path,
                          'RestAuth.Users.validators.UnknownValidator')


class BaseInstancetests(RestAuthTest):
    def test_user(self):
        u = UserInstance(5, 'foobar')
        self.assertEqual(u.id, 5)
        self.assertEqual(u.username, 'foobar')

    def test_group(self):
        g = GroupInstance(5, 'foobar', 'service')
        self.assertEqual(g.id, 5)
        self.assertEqual(g.name, 'foobar')
        self.assertEqual(g.service, 'service')


class BasicTests(RestAuthTest):
    def test_index(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)
