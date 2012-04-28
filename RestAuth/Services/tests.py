import base64, httplib

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test.client import RequestFactory, Client
from django.test import TestCase

import RestAuthCommon

from RestAuth.common import errors
from RestAuth.common.testdata import RestAuthTest
from RestAuth.Services.models import Service, service_create, ServiceUsernameNotValid
from Users import views

class BasicAuthTests(RestAuthTest): # GET /users/
    def setUp(self):
        if hasattr(self, 'settings'): # requires django-1.3.1:
            self.settings(LOGGING_CONFIG=None)
            
        self.c = Client()
        self.handler = RestAuthCommon.handlers.json()
        self.extra = {
            'HTTP_ACCEPT': self.handler.mime,
            'REMOTE_ADDR': '127.0.0.1',
            'content_type': self.handler.mime,
        }
        
    def set_auth(self, user, password):
        decoded = '%s:%s'%(user, password)
        header_value = "Basic %s"%(base64.b64encode(decoded.encode()).decode())
        self.extra['HTTP_AUTHORIZATION'] = header_value
    
    def tearDown(self):
        Service.objects.all().delete()
    
    def test_good_credentials(self):
        self.service = service_create('vowi', 'vowi', ['127.0.0.1', '::1'])
        u_ct = ContentType.objects.get(app_label="Users", model="serviceuser")
        p, c = Permission.objects.get_or_create(codename='users_list', content_type=u_ct,
                        defaults={'name': 'List all users'})
        self.service.user_permissions.add(p)
        
        self.set_auth('vowi', 'vowi')
        
        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [])
        
    def test_wrong_user(self):
        service_create('vowi', 'vowi', ['127.0.0.1', '::1'])
        self.set_auth('fsinf', 'vowi')
        
        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.UNAUTHORIZED)
        
    def test_wrong_password(self):
        service_create('vowi', 'vowi', ['127.0.0.1', '::1'])
        self.set_auth('vowi', 'fsinf')
        
        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.UNAUTHORIZED)
        
    def test_wrong_host(self):
        service = service_create('vowi', 'vowi', [])
        self.set_auth('vowi', 'vowi')
        
        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.UNAUTHORIZED)
        
        service.add_host('127.0.0.1')
        
        self.set_auth('vowi', 'vowi')
        self.extra['REMOTE_ADDR'] = '127.0.0.2'
        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.UNAUTHORIZED)
        
    def test_no_credentials(self):
        service_create('vowi', 'vowi', ['127.0.0.1', '::1'])
        self.set_auth('', '')
        
        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.UNAUTHORIZED)
        
    def test_no_auth_header(self):
        resp = self.get('/users/')
        self.assertEquals(resp.status_code, httplib.UNAUTHORIZED)
        
class ServiceHostTests(TestCase):
    """
    Test Service model, more specifically the hosts functionality. This is not exposed via
    the API.
    """
    def setUp(self):
        self.service = service_create('vowi', 'vowi', [])
    
    def tearDown(self):
        Service.objects.all().delete()
        
    def get_service(self):
        return Service.objects.get(username='vowi')
    
    def test_add_host(self):
        self.assertIsNone(self.service.add_host('127.0.0.1'))
        
        self.assertItemsEqual(self.get_service().hosts.values_list('address', flat=True),
                  ['127.0.0.1'])
        
    def test_set_hosts(self):
        hosts = ['127.0.0.1', '::1']
        self.assertIsNone(self.service.set_hosts(hosts))
        self.assertItemsEqual(self.get_service().hosts.values_list('address', flat=True),
                  hosts)
    
    def test_verify_host(self):
        hosts = ['127.0.0.1', '::1']
        self.assertIsNone(self.service.set_hosts(hosts))
        self.assertTrue(self.service.verify_host('127.0.0.1'))
        self.assertTrue(self.service.verify_host('::1'))
        
        self.assertFalse(self.service.verify_host('127.0.0.2'))
        self.assertFalse(self.service.verify_host('::2'))
        
    def test_verify(self):
        hosts = ['127.0.0.1', '::1']
        self.assertIsNone(self.service.set_hosts(hosts))
        
        self.assertTrue(self.service.verify('vowi', '127.0.0.1'))
        self.assertTrue(self.service.verify('vowi', '::1'))
        
        self.assertFalse(self.service.verify('wrong', '127.0.0.1'))
        self.assertFalse(self.service.verify('wrong', '::1'))
        
        self.assertFalse(self.service.verify('vowi', '127.0.0.2'))
        self.assertFalse(self.service.verify('vowi', '::2'))
    
    def test_del_host(self):
        self.service.add_host('127.0.0.1')
        self.assertItemsEqual(self.get_service().hosts.values_list('address', flat=True),
                  ['127.0.0.1'])
        
        self.assertIsNone(self.service.del_host('127.0.0.1'))
        self.assertItemsEqual(self.get_service().hosts.all(), [])
        
    def test_del_host_gone(self):
        self.assertItemsEqual(self.get_service().hosts.all(), [])
        self.assertIsNone(self.service.del_host('127.0.0.1'))
        self.assertItemsEqual(self.get_service().hosts.all(), [])
        
    def test_create_invalid_host(self):
        try:
            service_create('fs:inf', 'foobar', [])
            self.fail()
        except ServiceUsernameNotValid:
            self.assertItemsEqual(Service.objects.all(), [self.service])