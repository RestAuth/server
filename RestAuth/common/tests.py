# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

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
from common.content_handlers import get_handler
from common.content_handlers import load_handlers
from common.errors import UsernameInvalid
from common.middleware import RestAuthMiddleware
from common.testdata import RestAuthTest
from common.testdata import CliMixin
from common.testdata import capture
from common.testdata import group_backend
from common.testdata import groupname1
from common.testdata import groupname2
from common.testdata import groupname3
from common.testdata import groupname4
from common.testdata import property_backend
from common.testdata import propkey1
from common.testdata import propkey2
from common.testdata import propval1
from common.testdata import propval2
from common.testdata import propval3
from common.testdata import user_backend
from common.testdata import username1
from common.testdata import username2
from common.testdata import username3
from common.testdata import username4
from common.utils import import_path

restauth_import = getattr(__import__('bin.restauth-import'), 'restauth-import').main
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'hashers_passlib.apr_md5_crypt',
    'hashers_passlib.phpass',
)


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

class ContentHandlerTests(RestAuthTest):
    def test_load_handlers(self):
        with self.settings(CONTENT_HANDLERS=('foo.bar', )):
            self.assertRaises(ImproperlyConfigured, load_handlers)

        with self.settings(CONTENT_HANDLERS=('foobar', )):
            self.assertRaises(ImproperlyConfigured, load_handlers)

    def test_get_handler(self):
        handler = get_handler()
        self.assertTrue(isinstance(handler, handlers.ContentHandler))

    def test_get_wrong_handler(self):
        self.assertRaises(ValueError, get_handler, 'foo/bar')

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

    def test_non_ascii_whitespace(self):
        load_username_validators(('Users.validators.XMPPValidator', ))
        self.assertRaises(UsernameInvalid, validate_username, 'foo bar')
        validate_username('foobar')

    def test_email_check(self):
        load_username_validators(('Users.validators.EmailValidator', ))
        self.assertRaises(UsernameInvalid, validate_username, 'x' * 65)  # more then 64 chars
        validate_username('foobar')

    def test_mediawiki_check(self):
        load_username_validators(('Users.validators.MediaWikiValidator', ))
        with self.settings(MAX_USERNAME_LENGTH=500):
            self.assertRaises(UsernameInvalid, validate_username, 'x' * 256)
        validate_username('foobar')

    def test_linux_check(self):
        load_username_validators(('Users.validators.LinuxValidator', ))
        validate_username('foobar')

        self.assertRaises(UsernameInvalid, validate_username, 'x' * 33)
        self.assertRaises(UsernameInvalid, validate_username, '-foobar')

        with self.settings(RELAXED_LINUX_CHECKS=False):
            self.assertRaises(UsernameInvalid, validate_username, 'foo%bar')

    def test_drupal_check(self):
        load_username_validators(('Users.validators.DrupalValidator', ))
        self.assertRaises(UsernameInvalid, validate_username, ' foobar')
        self.assertRaises(UsernameInvalid, validate_username, 'foobar ')
        self.assertRaises(UsernameInvalid, validate_username, 'foo  bar')
        self.assertRaises(UsernameInvalid, validate_username, 'foo&bar')
        validate_username('foobar')

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
            except IOError as e:  # pragma: python2.6
                pass  # this throws IOError on python2.6.

        # invalid json data
        path = os.path.join(self.base, 'faulty1.json')
        with capture() as (stdout, stderr):
            try:
                restauth_import([path])
                self.fail('No exception thrown.')
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
                self.fail('No exception thrown.')
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
                self.fail('No exception thrown.')
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
                self.fail('No exception thrown.')
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
                self.fail('No exception thrown.')
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    ".*error: 'groups' does not appear to be a dictionary.")

        path = os.path.join(self.base, 'faulty6.json')
        with capture() as (stdout, stderr):
            restauth_import([path])
            self.assertEqual("""An error occured, rolling back transaction:
TypeError: 'password' is neither string nor dictionary.\n""", stderr.getvalue())

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
        # test various passwords:
        path = os.path.join(self.base, 'services3.json')
        with capture() as (stdout, stderr):
            restauth_import([path])

            self.assertEqual(stderr.getvalue(), '')
            self.assertHasLine(stdout, '^Services:$')
            self.assertHasLine(stdout, '^\* new1.example.com: Set password from input data.$')
            self.assertHasLine(stdout, '^\* new2.example.com: Set password from input data.$')
            self.assertHasLine(stdout, '^\* new3.example.com: Set password from input data.$')

        with override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS):
            load_hashers()
            self.assertTrue(Service.objects.get(
                username='new1.example.com').check_password('12345678'))
            self.assertTrue(Service.objects.get(
                username='new2.example.com').check_password('foobar'))
            self.assertTrue(Service.objects.get(
                username='new3.example.com').check_password('foobar'))
        load_hashers()

    def test_generate_service_hashes(self):
        path = os.path.join(self.base, 'services4.json')
        with capture() as (stdout, stderr):
            restauth_import(['--gen-passwords', path])

            self.assertEqual(stderr.getvalue(), '')
            self.assertHasLine(stdout, '^Services:$')
            self.assertHasLine(stdout, '^\* new.example.com: Generated password: .*$')
            match = re.search('Generated password: (.*)', stdout.getvalue())
            password = match.groups()[0]
            Service.objects.get(username='new.example.com').check_password(password)

    def test_set_hosts(self):
        path = os.path.join(self.base, 'services5.json')
        with capture() as (stdout, stderr):
            restauth_import([path])

            self.assertEqual(stderr.getvalue(), '')
            self.assertHasLine(stdout, '^Services:$')
            self.assertHasLine(stdout, '^\* new.example.com: Added service with no password.$')
            service = Service.objects.get(username='new.example.com')
            hosts = service.hosts.values_list('address', flat=True)
            self.assertItemsEqual(hosts, ['127.0.0.1', '::1'])

    def test_users(self, overwrite=False):
        path = os.path.join(self.base, 'users1.json')
        with capture() as (stdout, stderr):
            cmd = [path]
            if overwrite:
                cmd = ['--overwrite-properties', path]

            with override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS):
                restauth_import(cmd)
                self.assertHasLine(stdout, '^\* %s: Set hash from input data\.$' % username3)
                self.assertTrue(user_backend.check_password(username3, 'foobar'))

            self.assertItemsEqual(user_backend.list(), [username1, username2, username3])
            user = user_backend.get(username2)
            props = {
                propkey1: propval1,
                propkey2: propval2,
                # timestamps of when we wrote this test:
#                u'date joined': u'2013-12-01 19:27:50',
                u'last login': u'2013-12-01 19:27:44',
            }

            self.assertProperties(user, props)

    def test_users_django_hash(self, overwrite=False):
        path = os.path.join(self.base, 'users5.json')
        with capture() as (stdout, stderr):
            cmd = [path]
            if overwrite:
                cmd = ['--overwrite-properties', path]

            with override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS):
                restauth_import(cmd)
                self.assertHasLine(stdout, '^\* %s: Set hash from input data\.$' % username3)
                self.assertTrue(user_backend.check_password(username3, 'foobar'))
                self.assertItemsEqual(user_backend.list(), [username3])

    def test_users_overwrite_properties(self):
        self.test_users(overwrite=True)

    def test_skip_existing_users(self):
        user = user_backend.create(username2, property_backend=property_backend,
                                   properties={propkey1: propval3, })

        path = os.path.join(self.base, 'users1.json')
        with capture() as (stdout, stderr):
            restauth_import(['--skip-existing-users', path])
        self.assertProperties(user, {propkey1: propval3, })

    def test_unknown_hash_algorithm(self):
        path = os.path.join(self.base, 'users2.json')
        with capture() as (stdout, stderr):
            restauth_import([path])
            self.assertHasLine(
                stdout, '^\* %s: Hash of type "unknown" is not supported, skipping\.$' % username1)

    def test_existing_properties(self):
        user = user_backend.create(username2, property_backend=property_backend)
        property_backend.create(user, propkey1, propval3)  # propval1 is in json file

        path = os.path.join(self.base, 'users1.json')
        with capture() as (stdout, stderr):
            cmd = [path]
            restauth_import(cmd)
            self.assertItemsEqual(user_backend.list(), [username1, username2, username3])
            user = user_backend.get(username2)

            pattern = '^%s: Property "%s" already exists\.$' % (username2, propkey1)
            self.assertHasLine(stdout, pattern)
            self.assertHasLine(stdout, '^%s: Property "date joined" already exists\.$' % username2)

            expected_props = {
                propkey1: propval3,  # propva1 is in json-file - we don't overwrite!
                propkey2: propval2,
                u'last login': u'2013-12-01 19:27:44',  # date from json file
            }

            props = property_backend.list(user)
            # delete 'date joined' prop because it was created by the user_backend and
            # restauth-import doesn't overwrite in this invocation:
            del props['date joined']

            self.assertEqual(props, expected_props)

    def test_gen_passwords(self):
        path = os.path.join(self.base, 'users3.json')
        with capture() as (stdout, stderr):
            restauth_import(['--gen-passwords', path])
            output = stdout.getvalue()
            self.assertHasLine(output, '^\* %s: Generated password: .*' % username1)
            password = re.search('Generated password: (.*)', output).groups()[0]
        self.assertTrue(user_backend.check_password(username1, password))

    def test_wrong_password_type(self):
        path = os.path.join(self.base, 'users4.json')
        with capture() as (stdout, stderr):
            restauth_import([path])
            self.assertEqual(stdout.getvalue(), 'Users:\n')
            self.assertHasLine(stderr, '^TypeError: password is of type list$')

    def test_groups(self):
        user1 = user_backend.create(username1, property_backend=property_backend)
        user2 = user_backend.create(username2, property_backend=property_backend)
        user3 = user_backend.create(username3, property_backend=property_backend)

        path = os.path.join(self.base, 'groups1.json')
        with capture() as (stdout, stderr):
            restauth_import([path])
            self.assertHasLine(stdout, '^Groups:$')
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname1)
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname2)
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname3)
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname4)

        # get groups from backend
        group1 = group_backend.get(groupname1)
        group2 = group_backend.get(groupname2, service=self.service)
        group3 = group_backend.get(groupname3, service=self.service)
        group4 = group_backend.get(groupname4)

        # test memberships
        self.assertItemsEqual(group_backend.members(group1), [])
        self.assertItemsEqual(group_backend.members(group2), [username1, username2])
        self.assertItemsEqual(group_backend.members(group3), [username1, username2, username3])
        self.assertItemsEqual(group_backend.members(group4), [username1, username2])

    def test_existing_groups(self):
        user1 = user_backend.create(username1, property_backend=property_backend)
        user2 = user_backend.create(username2, property_backend=property_backend)
        user3 = user_backend.create(username3, property_backend=property_backend)
        user4 = user_backend.create(username4, property_backend=property_backend)  # new user

        # this group already exists and has some memberships
        group2 = group_backend.create(groupname2, service=self.service)
        group_backend.add_user(group2, user1)
        group_backend.add_user(group2, user4)

        path = os.path.join(self.base, 'groups1.json')
        with capture() as (stdout, stderr):
            restauth_import([path])
            self.assertHasLine(stdout, '^Groups:$')
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname1)
            self.assertHasLine(stdout, '^\* %s: Already exists, adding memberships\.$' % groupname2)
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname3)
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname4)

        # get groups from backend
        group1 = group_backend.get(groupname1)
        group3 = group_backend.get(groupname3, service=self.service)
        group4 = group_backend.get(groupname4)

        # test memberships
        self.assertItemsEqual(group_backend.members(group1), [])
        self.assertItemsEqual(group_backend.members(group2), [username1, username2, username4])
        self.assertItemsEqual(group_backend.members(group3), [username1, username2, username3,
                                                              username4])
        self.assertItemsEqual(group_backend.members(group4), [username1, username2, username4])

    def test_skip_existing_groups(self):
        # same test-setup as above, only we skip existing groups
        user1 = user_backend.create(username1, property_backend=property_backend)
        user2 = user_backend.create(username2, property_backend=property_backend)
        user3 = user_backend.create(username3, property_backend=property_backend)
        user4 = user_backend.create(username4, property_backend=property_backend)  # new user

        # this group already exists and has some memberships
        group2 = group_backend.create(groupname2, service=self.service)
        group_backend.add_user(group2, user1)
        group_backend.add_user(group2, user4)

        path = os.path.join(self.base, 'groups1.json')
        with capture() as (stdout, stderr):
            try:
                restauth_import(['--skip-existing-groups', path])
            except SystemExit:
                self.fail(stderr.getvalue())
            self.assertHasLine(stdout, '^Groups:$')
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname1)
            self.assertHasLine(stdout, '^\* %s: Already exists, skipping\.$' % groupname2)
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname3)
            self.assertHasLine(stdout, '^\* %s: created\.$' % groupname4)

        # get groups from backend
        group1 = group_backend.get(groupname1)
        group3 = group_backend.get(groupname3, service=self.service)
        group4 = group_backend.get(groupname4)

        # test memberships
        self.assertItemsEqual(group_backend.members(group1), [])
        self.assertItemsEqual(group_backend.members(group2), [username1, username4])
        # group3 now is not a subgroup, because group2 already existed and we skipped its data
        self.assertEqual(group_backend.members(group3), [username3])
        self.assertEqual(group_backend.members(group4), [])
