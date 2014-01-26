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

from base64 import b64encode

from django.contrib.auth.models import Permission
from django.contrib.auth import authenticate
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from django.utils.six.moves import http_client

import RestAuthCommon

from Services.models import Service
from Services.models import ServiceUsernameNotValid
from Services.models import service_create
from Services.models import get_service_hasher
from Services.models import load_service_hasher
from common.testdata import CliMixin
from common.testdata import RestAuthTest
from common.testdata import password1
from common.testdata import password2
from common.testdata import servicename1
from common.testdata import servicename2
from common.testdata import servicename3
from common.testdata import servicename4
from common.testdata import servicename5
from common.testdata import capture

PATHS = [
    (['get', 'post'], '/users/'),
    (['get', 'post', 'put', 'delete'], '/users/user/'),
    (['get', 'post', 'put'], '/users/user/props/'),
    (['get', 'put', 'delete'], '/users/user/props/prop/'),
    (['get', 'post'], '/groups/'),
    (['get', 'delete'], '/groups/group/'),
    (['get', 'post'], '/groups/group/users/'),
    (['get', 'delete'], '/groups/group/users/user/'),
    (['get', 'post'], '/groups/group/groups/'),
    (['delete'], '/groups/group/groups/group/'),
]
cli = getattr(__import__('bin.restauth-service'), 'restauth-service').main

@override_settings(LOGGING_CONFIG=None)
class BasicAuthTests(RestAuthTest):  # GET /users/
    def setUp(self):
        self.c = Client()
        self.handler = RestAuthCommon.handlers.json()
        self.extra = {
            'HTTP_ACCEPT': self.handler.mime,
            'REMOTE_ADDR': '127.0.0.1',
            'content_type': self.handler.mime,
        }
        cache.clear()

    def set_auth(self, user, password):
        decoded = '%s:%s' % (user, password)
        header_value = "Basic %s" % (b64encode(decoded.encode()).decode())
        self.extra['HTTP_AUTHORIZATION'] = header_value

    def tearDown(self):
        Service.objects.all().delete()

    def test_good_credentials(self):
        self.service = service_create('vowi', 'vowi', '127.0.0.1', '::1')
        u_ct = ContentType.objects.get(app_label="Users", model="serviceuser")
        p, c = Permission.objects.get_or_create(
            codename='users_list', content_type=u_ct,
            defaults={'name': 'List all users'}
        )
        self.service.user_permissions.add(p)

        self.set_auth('vowi', 'vowi')

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [])

    def test_permission_denied(self):
        self.service = service_create('vowi', 'vowi', '127.0.0.1', '::1')
        self.set_auth('vowi', 'vowi')

        for methods, path in PATHS:
            for method in methods:
                if method in ['post', 'put']:
                    resp = getattr(self, method)(path, {})
                else:
                    resp = getattr(self, method)(path)
                self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        # manually handle /groups/?user=foobar
        resp = self.get('/groups/', {'user': 'whatever'})
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_method_now_allowed(self):
        self.service = service_create('vowi', 'vowi', '127.0.0.1', '::1')
        self.set_auth('vowi', 'vowi')

        for good_methods, path in PATHS:
            for method in ['get', 'post', 'put', 'delete']:
                if method not in good_methods:
                    if method in ['post', 'put']:
                        resp = getattr(self, method)(path, {})
                    else:
                        resp = getattr(self, method)(path)
                    self.assertEqual(resp.status_code,
                                      http_client.METHOD_NOT_ALLOWED)

    def test_wrong_user(self):
        service_create('vowi', 'vowi', '127.0.0.1', '::1')
        self.set_auth('fsinf', 'vowi')

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, http_client.UNAUTHORIZED)

    def test_wrong_password(self):
        service_create('vowi', 'vowi', '127.0.0.1', '::1')
        self.set_auth('vowi', 'fsinf')

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, http_client.UNAUTHORIZED)

    def test_wrong_host(self):
        service = service_create('vowi', 'vowi')
        self.set_auth('vowi', 'vowi')

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, http_client.UNAUTHORIZED)

        service.add_hosts('127.0.0.1')

        self.set_auth('vowi', 'vowi')
        self.extra['REMOTE_ADDR'] = '127.0.0.2'
        resp = self.get('/users/')
        self.assertEqual(resp.status_code, http_client.UNAUTHORIZED)

    def test_no_credentials(self):
        service_create('vowi', 'vowi', '127.0.0.1', '::1')
        self.set_auth('', '')

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, http_client.UNAUTHORIZED)

    def test_no_auth_header(self):
        resp = self.get('/users/')
        self.assertEqual(resp.status_code, http_client.UNAUTHORIZED)


class ServiceHostTests(TestCase):
    """
    Test Service model, more specifically the hosts functionality. This is not
    exposed via the API.
    """
    def setUp(self):
        self.service = service_create('vowi', 'vowi')

    def tearDown(self):
        Service.objects.all().delete()

    def get_service(self):
        return Service.objects.get(username='vowi')

    def get_hosts(self):
        return self.get_service().hosts.values_list('address', flat=True)

    def assertItemsEqual(self, actual, expected, msg=None):
        """This method is not present in python3."""
        try:
            super(ServiceHostTests, self).assertItemsEqual(
                actual, expected, msg)
        except AttributeError:
            self.assertEqual(set(actual), set(expected), msg)
            self.assertEqual(len(actual), len(expected))

    def test_add_host(self):
        hosts = ['127.0.0.1']
        self.assertIsNone(self.service.add_hosts(*hosts))
        self.assertItemsEqual(self.get_hosts(), hosts)

    def test_set_hosts(self):
        hosts = ['127.0.0.1', '::1']
        self.assertIsNone(self.service.set_hosts(*hosts))
        # Warning: using assertItemsEqual fails in python2.6 in the next line
        self.assertItemsEqual(self.get_hosts(), hosts)

    def test_verify_host(self):
        hosts = ['127.0.0.1', '::1']
        self.assertIsNone(self.service.set_hosts(*hosts))
        self.assertTrue(self.service.verify_host('127.0.0.1'))
        self.assertTrue(self.service.verify_host('::1'))

        self.assertFalse(self.service.verify_host('127.0.0.2'))
        self.assertFalse(self.service.verify_host('::2'))

    def test_verify(self):
        hosts = ['127.0.0.1', '::1']
        self.assertIsNone(self.service.set_hosts(*hosts))

        self.assertTrue(self.service.verify('vowi', '127.0.0.1'))
        self.assertTrue(self.service.verify('vowi', '::1'))

        self.assertFalse(self.service.verify('wrong', '127.0.0.1'))
        self.assertFalse(self.service.verify('wrong', '::1'))

        self.assertFalse(self.service.verify('vowi', '127.0.0.2'))
        self.assertFalse(self.service.verify('vowi', '::2'))

    def test_del_hosts(self):
        hosts = ['127.0.0.1']
        self.service.add_hosts(*hosts)
        self.assertItemsEqual(self.get_hosts(), hosts)

        self.assertIsNone(self.service.del_hosts(*hosts))
        self.assertItemsEqual(self.get_service().hosts.all(), [])

    def test_del_hosts_gone(self):
        self.assertItemsEqual(self.get_service().hosts.all(), [])
        self.assertIsNone(self.service.del_hosts(*['127.0.0.1']))
        self.assertItemsEqual(self.get_service().hosts.all(), [])

    def test_create_invalid_host(self):
        try:
            service_create('fs:inf', 'foobar')
            self.fail()
        except ServiceUsernameNotValid:
            self.assertItemsEqual(Service.objects.all(), [self.service])


class AuthBackendTests(RestAuthTest):
    def setUp(self):
        self.service = Service.objects.create(username=servicename1)
        self.service.add_hosts('::1')
        self.service.set_password('nopass')
        self.service.save()

    def auth(self, service, password, host='::1', method='Basic'):
        raw = '%s:%s' % (service.name, password)
        encoded = b64encode(raw.encode()).decode()
        header = '%s %s' % (method, encoded)
        return authenticate(header=header, host=host)

    def test_auth(self):
        self.assertTrue(self.auth(self.service, 'nopass'))
        self.assertTrue(self.auth(self.service, 'nopass'))
        self.assertTrue(self.auth(self.service, 'falsepass') is None)
        self.assertTrue(self.auth(self.service, 'falsepass') is None)

    def test_wrong_service(self):
        class bogus_cls:
            name = servicename2
        self.assertTrue(self.auth(bogus_cls, 'nopass', '::1') is None)
        self.assertTrue(self.auth(bogus_cls, 'nopass', '::1') is None)

    def test_wrong_pass(self):
        self.assertTrue(self.auth(self.service, 'falsepass') is None)
        self.assertTrue(self.auth(self.service, 'falsepass') is None)

    def test_wrong_host(self):
        self.assertTrue(self.auth(self.service, 'nopass', '::2') is None)
        self.assertTrue(self.auth(self.service, 'nopass', '::2') is None)

    def test_wrong_method(self):
        self.assertTrue(self.auth(self.service, 'nopass', method='foobar') is None)
        self.assertTrue(self.auth(self.service, 'nopass', method='foobar') is None)

    def test_wrong_format(self):
        password = 'nopass'
        host = '::1'

        raw = '%s%s' % (self.service.name, password)
        encoded = b64encode(raw.encode()).decode()
        header = '%s %s' % ('Basic', encoded)
        self.assertTrue(authenticate(header=header, host=host) is None)

        raw = '%s%s' % (self.service.name, password)
        encoded = b64encode(raw.encode()).decode() + 'fppbasdf'
        header = '%s %s' % ('Basic', encoded)
        self.assertTrue(authenticate(header=header, host=host) is None)


    def test_no_cache(self):
        with self.settings(SECURE_CACHE=False):
            self.test_auth()
            self.test_wrong_service()
            self.test_wrong_pass()
            self.test_wrong_host()
            self.test_wrong_method()
            self.test_wrong_format()


class ServiceHasherTests(RestAuthTest):
    def test_default(self):
        hasher = 'hashers_passlib.phpass'

        with self.settings(SERVICE_PASSWORD_HASHER='default', PASSWORD_HASHERS=(hasher, )):
            load_service_hasher()
            hasher = get_service_hasher()
            self.assertEqual(hasher.algorithm, 'phpass')

    def test_wrong_hasher(self):
        with self.settings(SERVICE_PASSWORD_HASHER='foobar.blahugo'):
            self.assertRaises(ImproperlyConfigured, load_service_hasher)

    def test_unknown(self):
        hasher = 'foobar.phpass'

        with self.settings(SERVICE_PASSWORD_HASHER=hasher, PASSWORD_HASHERS=(hasher, )):
            self.assertRaises(ImproperlyConfigured, load_service_hasher)

    def tearDown(self):
        load_service_hasher()


class CliTests(RestAuthTest, CliMixin):
    def test_add(self):
        with capture() as (stdout, stderr):
            cli(['add', '--password=foobar', servicename4])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertTrue(Service.objects.get(username=servicename4).check_password('foobar'))

    def test_add_existing(self):
        s = Service.objects.create(username=servicename3)
        s.set_password(password1)
        s.save()

        with capture() as (stdout, stderr):
            with transaction.atomic():
                try:
                    cli(['add', '--password=%s' % password2, servicename3])
                    self.fail("Adding an existing service should be an error.")
                except SystemExit as e:
                    self.assertEqual(e.code, 2)
                    self.assertEqual(stdout.getvalue(), '')
                    self.assertHasLine(stderr, 'Service already exists.$')

        self.assertTrue(Service.objects.get(username=servicename3).check_password(password1))

    def test_add_invalid(self):
        servicename = 'foo:bar'

        with capture() as (stdout, stderr):
            try:
                cli(['add', '--password=%s' % password2, servicename])
                self.fail("Adding an existing service should be an error.")
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'Service name must not contain a \':\'$')

        self.assertFalse(Service.objects.filter(username=servicename).exists())

    def test_add_gen_password(self):
        with capture() as (stdout, stderr):
            cli(['add', '--gen-password', servicename4])
            self.assertEqual(stderr.getvalue(), '')
            password = stdout.getvalue().strip()
            self.assertTrue(len(password) > 12)
        self.assertTrue(Service.objects.get(username=servicename4).check_password(password))

    def test_rename(self):
        Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            cli(['rename', servicename5, servicename4])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertTrue(Service.objects.filter(username=servicename4).exists())
        self.assertFalse(Service.objects.filter(username=servicename5).exists())

    def test_rename_service_not_existing(self):
        with capture() as (stdout, stderr):
            try:
                cli(['rename', servicename5, servicename4])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'Service does not exist\.$')
        self.assertFalse(Service.objects.filter(username=servicename4).exists())
        self.assertFalse(Service.objects.filter(username=servicename5).exists())

    def test_rename_exists(self):
        Service.objects.create(username=servicename4)
        Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            try:
                cli(['rename', servicename5, servicename4])
                self.fail('Rename does not fail.')
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'error: %s: Service already exists\.$' % servicename4)
        self.assertTrue(Service.objects.filter(username=servicename4).exists())
        self.assertTrue(Service.objects.filter(username=servicename5).exists())

    def test_rm(self):
        Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            cli(['rm', servicename5])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertFalse(Service.objects.filter(username=servicename5).exists())

    def test_ls(self):
        with capture() as (stdout, stderr):
            cli(['ls'])
            hosts = ', '.join(self.service.addresses)
            self.assertEqual(stdout.getvalue(), '%s: %s\n' % (self.service.name, hosts))
            self.assertEqual(stderr.getvalue(), '')

    def test_view(self):
        self.maxDiff = None
        with capture() as (stdout, stderr):
            cli(['view', self.service.name])
            self.assertEqual(stdout.getvalue(), """Last used: %s
Hosts: %s
Permissions: %s
""" % (self.service.last_login, ', '.join(self.service.addresses), ', '.join(self.service.permissions)))
            self.assertEqual(stderr.getvalue(), '')

    def test_set_hosts(self):
        s = Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            cli(['set-hosts', servicename5, '127.0.0.1'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertItemsEqual(s.hosts.values_list('address', flat=True), ['127.0.0.1'])

        # test if second set overwrites the first host
        with capture() as (stdout, stderr):
            cli(['set-hosts', servicename5, '::1'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertItemsEqual(s.hosts.values_list('address', flat=True), ['::1'])

    def test_set_hosts_error(self):
        s = Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            try:
                cli(['set-hosts', servicename5, 'wrong hostname'])
                self.fail("wrong hostname doesn't exit")
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'error: Enter a valid IPv4 or IPv6 address.$')
        self.assertItemsEqual(s.hosts.values_list('address', flat=True), [])

    def test_add_hosts(self):
        s = Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            cli(['add-hosts', servicename5, '127.0.0.1'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertItemsEqual(s.hosts.values_list('address', flat=True), ['127.0.0.1'])

        # test if second add doesn't overwrite the first host
        with capture() as (stdout, stderr):
            cli(['add-hosts', servicename5, '::1'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertItemsEqual(s.hosts.values_list('address', flat=True), ['127.0.0.1', '::1'])

    def test_add_hosts_error(self):
        s = Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            try:
                cli(['add-hosts', servicename5, 'wrong hostname'])
                self.fail("wrong hostname doesn't exit")
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'error: Enter a valid IPv4 or IPv6 address.$')
        self.assertItemsEqual(s.hosts.values_list('address', flat=True), [])

    def test_rm_hosts(self):
        s = Service.objects.create(username=servicename5)
        s.add_hosts('127.0.0.1')

        with capture() as (stdout, stderr):
            cli(['rm-hosts', servicename5, '127.0.0.1'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertItemsEqual(s.hosts.values_list('address', flat=True), [])

    def test_set_password(self):
        s = Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            cli(['set-password', servicename5, '--password', password1])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertTrue(Service.objects.get(username=s.name).check_password(password1))

    def test_set_password_generated(self):
        s = Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            cli(['set-password', servicename5, '--gen-password'])
            gen_password = stdout.getvalue().strip()
            self.assertEqual(stderr.getvalue(), '')
        s = Service.objects.get(username=s.name)
        self.assertFalse(s.check_password(password1))
        self.assertTrue(s.check_password(gen_password))

    def test_set_permissions(self):
        s = Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            cli(['set-permissions', servicename5, 'users_list'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        s = Service.objects.get(username=servicename5)
        self.assertTrue(s.has_perm('Users.users_list'))

        with capture() as (stdout, stderr):
            cli(['set-permissions', servicename5, 'props_list', 'groups_list'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        s = Service.objects.get(username=servicename5)
        self.assertTrue(s.has_perm('Users.props_list'))
        self.assertTrue(s.has_perm('Groups.groups_list'))
        self.assertFalse(s.has_perm('Users.users_list'))

    def test_add_permissions(self):
        s = Service.objects.create(username=servicename5)

        with capture() as (stdout, stderr):
            cli(['add-permissions', servicename5, 'users_list'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        s = Service.objects.get(username=servicename5)
        self.assertTrue(s.has_perm('Users.users_list'))

        with capture() as (stdout, stderr):
            cli(['add-permissions', servicename5, 'props_list', 'groups_list'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        s = Service.objects.get(username=servicename5)
        self.assertTrue(s.has_perm('Users.props_list'))
        self.assertTrue(s.has_perm('Groups.groups_list'))
        self.assertTrue(s.has_perm('Users.users_list'))

    def test_rm_permissions(self):
        s = Service.objects.create(username=servicename5)
        with capture() as (stdout, stderr):
            cli(['set-permissions', servicename5, 'props_list', 'groups_list'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        s = Service.objects.get(username=servicename5)
        self.assertTrue(s.has_perm('Users.props_list'))
        self.assertTrue(s.has_perm('Groups.groups_list'))

        # remove perm again
        with capture() as (stdout, stderr):
            cli(['rm-permissions', servicename5, 'props_list'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        s = Service.objects.get(username=servicename5)
        self.assertFalse(s.has_perm('Users.props_list'))
        self.assertTrue(s.has_perm('Groups.groups_list'))
