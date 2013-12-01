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

import os
import re

from django.contrib.auth.hashers import load_hashers
from django.core.exceptions import ImproperlyConfigured
from django.test.client import Client
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.utils.unittest import TestCase

from django.utils.six.moves import http_client

from RestAuthCommon import handlers

from Services.models import Service
from Users.validators import Validator
from Users.validators import get_validators
from Users.validators import load_username_validators
from Users.validators import validate_username
from backends.base import GroupInstance
from backends.base import UserInstance
from common.errors import UsernameInvalid
from common.middleware import RestAuthMiddleware
from common.testdata import RestAuthTest
from common.testdata import CliMixin
from common.testdata import capture
from common.testdata import user_backend
from common.testdata import username1
from common.utils import import_path

restauth_import = getattr(__import__('bin.restauth-import'), 'restauth-import').main


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
    'Users.validators.EmailValidator',
    'Users.validators.MediaWikiValidator',
    'Users.validators.LinuxValidator',
    'Users.validators.WindowsValidator',
    'Users.validators.XMPPValidator',
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
            'Users.validators.MediaWikiValidator',
        ))

        # substract 1 because one validator has no 'check' method:
        self.assert_validators((
            'Users.validators.EmailValidator',
            'Users.validators.MediaWikiValidator',
            'Users.validators.XMPPValidator',  # no check method!
        ), substract=1)


class ImportTests(RestAuthTest):
    def test_malformed_path(self):
        self.assertRaises(ImproperlyConfigured, import_path, 'foobar')

    def test_unknown_path(self):
        self.assertRaises(ImproperlyConfigured, import_path,
                          'Unknown.Module')

    def test_unkown_class(self):
        self.assertRaises(ImproperlyConfigured, import_path,
                          'Users.validators.UnknownValidator')


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


class RestAuthImportTests(RestAuthTest, CliMixin):
    base = os.path.join(os.path.dirname(__file__), 'testdata')

    def test_basic(self):
        with capture() as (stdout, stderr):
            try:
                restauth_import(['-h'])
                self.fail('-h does not exit')
            except SystemExit as e:
                self.assertEqual(e.code, 0)

    def test_faulty(self):
        path = os.path.join(self.base, 'file-not-found.json')
        with capture() as (stdout, stderr):
            try:
                restauth_import([path])
            except SystemExit as e:
                self.assertEqual(e.code, 2)

        # invalid json data
        path = os.path.join(self.base, 'faulty1.json')
        with capture() as (stdout, stderr):
            try:
                restauth_import([path])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    '.*error: %s: No JSON object could be decoded$' % path)

        # top-level not a dict:
        path = os.path.join(self.base, 'faulty2.json')
        with capture() as (stdout, stderr):
            try:
                restauth_import([path])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    '.*error: %s: Top-level data structure must be a dictionary.$' % path)

        # services/users/groups not a dict
        path = os.path.join(self.base, 'faulty3.json')
        with capture() as (stdout, stderr):
            try:
                restauth_import([path])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    ".*error: 'services' does not appear to be a dictionary.")
        path = os.path.join(self.base, 'faulty4.json')
        with capture() as (stdout, stderr):
            try:
                restauth_import([path])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    ".*error: 'users' does not appear to be a dictionary.")
        path = os.path.join(self.base, 'faulty5.json')
        with capture() as (stdout, stderr):
            try:
                restauth_import([path])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    ".*error: 'groups' does not appear to be a dictionary.")

    def test_empty(self):
        for i in range(1, 6):
            path = os.path.join(self.base, 'empty%s.json' % i)
            with capture() as (stdout, stderr):
                restauth_import([path])
                self.assertEqual(stdout.getvalue(), '')
                self.assertEqual(stderr.getvalue(), '')

    def test_services(self):
        # already exists:
        path = os.path.join(self.base, 'services1.json')
        with capture() as (stdout, stderr):
            restauth_import([path])
            self.assertHasLine(stdout, '^Services:$')
            self.assertHasLine(stdout, '^\* %s: Already exists.$' % self.service.username)
            self.assertEqual(stderr.getvalue(), '')

        service_name = 'new.example.com'

        # raw password
        path = os.path.join(self.base, 'services2.json')
        with capture() as (stdout, stderr):
            restauth_import([path])
            self.assertHasLine(stdout, '^Services:$')
            self.assertHasLine(stdout, '^\* %s: Set password from input data.$' % service_name)
            self.assertEqual(stderr.getvalue(), '')
            self.assertTrue(Service.objects.get(username=service_name).check_password('foobar'))

    def test_service_hashes(self):
        PASSWORD_HASHERS = (
            'django.contrib.auth.hashers.PBKDF2PasswordHasher',
            'django.contrib.auth.hashers.MD5PasswordHasher',
            'common.hashers.Apr1Hasher',
            'common.hashers.PhpassHasher',
        )
        # test various passwords:
        path = os.path.join(self.base, 'services3.json')
        with capture() as (stdout, stderr):
            restauth_import([path])

            self.assertEqual(stderr.getvalue(), '')
            self.assertHasLine(stdout, '^Services:$')
            self.assertHasLine(
                stdout, '^\* new1.example.com: Set password from input data.$')
            self.assertHasLine(
                stdout, '^\* new2.example.com: Set password from input data.$')
            self.assertHasLine(
                stdout, '^\* new3.example.com: Set password from input data.$')

        with override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS):
            load_hashers()
            self.assertTrue(Service.objects.get(
                username='new1.example.com').check_password('12345678'))
            self.assertTrue(Service.objects.get(
                username='new2.example.com').check_password('foobar'))
            self.assertTrue(Service.objects.get(
                username='new3.example.com').check_password('foobar'))
        load_hashers()

    def test_generate_hashes(self):
        path = os.path.join(self.base, 'services4.json')
        with capture() as (stdout, stderr):
            try:
                restauth_import(['--gen-passwords', path])
            except SystemExit as e:
                self.fail(stderr.getvalue())

            self.assertEqual(stderr.getvalue(), '')
            self.assertHasLine(stdout, '^Services:$')
            self.assertHasLine(
                stdout, '^\* new.example.com: Generated password: .*$')
            match = re.search('Generated password: (.*)', stdout.getvalue())
            password = match.groups()[0]
            Service.objects.get(username='new.example.com').check_password(
                password)
