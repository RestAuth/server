from base64 import b64encode
try:
    import httplib as httpclient  # python 2.x
except ImportError:
    from http import client as httpclient  # python 3.x

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

import RestAuthCommon

from RestAuth.common.testdata import RestAuthTest
from RestAuth.Services.models import Service
from RestAuth.Services.models import service_create
from RestAuth.Services.models import ServiceUsernameNotValid

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
        self.assertEqual(resp.status_code, httpclient.OK)
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
                self.assertEqual(resp.status_code, httpclient.FORBIDDEN)

        # manually handle /groups/?user=foobar
        resp = self.get('/groups/', {'user': 'whatever'})
        self.assertEqual(resp.status_code, httpclient.FORBIDDEN)

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
                                      httpclient.METHOD_NOT_ALLOWED)

    def test_wrong_user(self):
        service_create('vowi', 'vowi', '127.0.0.1', '::1')
        self.set_auth('fsinf', 'vowi')

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httpclient.UNAUTHORIZED)

    def test_wrong_password(self):
        service_create('vowi', 'vowi', '127.0.0.1', '::1')
        self.set_auth('vowi', 'fsinf')

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httpclient.UNAUTHORIZED)

    def test_wrong_host(self):
        service = service_create('vowi', 'vowi')
        self.set_auth('vowi', 'vowi')

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httpclient.UNAUTHORIZED)

        service.add_hosts('127.0.0.1')

        self.set_auth('vowi', 'vowi')
        self.extra['REMOTE_ADDR'] = '127.0.0.2'
        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httpclient.UNAUTHORIZED)

    def test_no_credentials(self):
        service_create('vowi', 'vowi', '127.0.0.1', '::1')
        self.set_auth('', '')

        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httpclient.UNAUTHORIZED)

    def test_no_auth_header(self):
        resp = self.get('/users/')
        self.assertEqual(resp.status_code, httpclient.UNAUTHORIZED)


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
