import base64, httplib

from django.conf import settings
from django.test.client import RequestFactory
from django.test import TestCase

import RestAuthCommon

from RestAuth.common import errors
from RestAuth.common.testdata import RestAuthTest
from RestAuth.Services.models import Service, service_create, ServiceUsernameNotValid
from Users import views

class BasicAuthTests( RestAuthTest ): # GET /users/
	def setUp( self ):
		if hasattr( self, 'settings' ): # requires django-1.3.1:
			self.settings( LOGGING_CONFIG=None )

		self.factory = RequestFactory()
		self.content_handler = RestAuthCommon.handlers.json()
		
	def set_auth( self, user, password ):
		decoded = '%s:%s'%(user, password)
		self.authorization = "Basic %s"%(base64.b64encode( decoded.encode() ).decode() )
	
	def tearDown( self ):
		Service.objects.all().delete()
	
	def test_good_credentials( self ):
		service_create( 'vowi', 'vowi', [ '127.0.0.1', '::1' ] )
		self.set_auth( 'vowi', 'vowi' )
		
		request = self.get( '/users/' )
		resp = views.index( request )
		self.assertEquals( resp.status_code, httplib.OK )
		self.assertItemsEqual( self.parse( resp, 'list' ), [] )
		
	def test_wrong_user( self ):
		service_create( 'vowi', 'vowi', [ '127.0.0.1', '::1' ] )
		self.set_auth( 'fsinf', 'vowi' )
		
		request = self.get( '/users/' )
		resp = views.index( request )
		self.assertEquals( resp.status_code, httplib.UNAUTHORIZED )
		
	def test_wrong_password( self ):
		service_create( 'vowi', 'vowi', [ '127.0.0.1', '::1' ] )
		self.set_auth( 'vowi', 'fsinf' )
		
		request = self.get( '/users/' )
		resp = views.index( request )
		self.assertEquals( resp.status_code, httplib.UNAUTHORIZED )
		
	def test_wrong_host( self ):
		service_create( 'vowi', 'vowi', [] )
		self.set_auth( 'vowi', 'vowi' )
		
		request = self.get( '/users/' )
		resp = views.index( request )
		self.assertEquals( resp.status_code, httplib.UNAUTHORIZED )
		
	def test_no_credentials( self ):
		service_create( 'vowi', 'vowi', [ '127.0.0.1', '::1' ] )
		self.set_auth( '', '' )
		
		request = self.get( '/users/' )
		resp = views.index( request )
		self.assertEquals( resp.status_code, httplib.UNAUTHORIZED )
		
	def test_no_auht_header( self ):
		request = getattr( self.factory, 'get' )( '/users/' )
		request.META['HTTP_ACCEPT'] = self.content_handler.mime

		resp = views.index( request )
		self.assertEquals( resp.status_code, httplib.UNAUTHORIZED )
		
class ServiceHostTests( TestCase ):
	"""
	Test Service model, more specifically the hosts functionality. This is not exposed via
	the API.
	"""
	def setUp( self ):
		self.service = service_create( 'vowi', 'vowi', [] )
	
	def tearDown( self ):
		Service.objects.all().delete()
		
	def get_service( self ):
		return Service.objects.get( username='vowi' )
	
	def test_add_host( self ):
		self.assertIsNone( self.service.add_host( '127.0.0.1' ) )
		
		self.assertItemsEqual( self.get_service().hosts.values_list( 'address', flat=True ),
				  ['127.0.0.1'] )
		
	def test_set_hosts( self ):
		hosts = [ '127.0.0.1', '::1' ]
		self.assertIsNone( self.service.set_hosts( hosts ) )
		self.assertItemsEqual( self.get_service().hosts.values_list( 'address', flat=True ),
				  hosts )
	
	def test_verify_host( self ):
		hosts = [ '127.0.0.1', '::1' ]
		self.assertIsNone( self.service.set_hosts( hosts ) )
		self.assertTrue( self.service.verify_host( '127.0.0.1' ) )
		self.assertTrue( self.service.verify_host( '::1' ) )
		
		self.assertFalse( self.service.verify_host( '127.0.0.2' ) )
		self.assertFalse( self.service.verify_host( '::2' ) )
		
	def test_verify( self ):
		hosts = [ '127.0.0.1', '::1' ]
		self.assertIsNone( self.service.set_hosts( hosts ) )
		
		self.assertTrue( self.service.verify( 'vowi', '127.0.0.1' ) )
		self.assertTrue( self.service.verify( 'vowi', '::1' ) )
		
		self.assertFalse( self.service.verify( 'wrong', '127.0.0.1' ) )
		self.assertFalse( self.service.verify( 'wrong', '::1' ) )
		
		self.assertFalse( self.service.verify( 'vowi', '127.0.0.2' ) )
		self.assertFalse( self.service.verify( 'vowi', '::2' ) )
	
	def test_del_host( self ):
		self.service.add_host( '127.0.0.1' )
		self.assertItemsEqual( self.get_service().hosts.values_list( 'address', flat=True ),
				  ['127.0.0.1'] )
		
		self.assertIsNone( self.service.del_host( '127.0.0.1' ) )
		self.assertItemsEqual( self.get_service().hosts.all(), [] )
		
	def test_del_host_gone( self ):
		self.assertItemsEqual( self.get_service().hosts.all(), [] )
		self.assertIsNone( self.service.del_host( '127.0.0.1' ) )
		self.assertItemsEqual( self.get_service().hosts.all(), [] )
		
	def test_create_invalid_host( self ):
		try:
			service_create( 'fs:inf', 'foobar', [] )
			self.fail()
		except ServiceUsernameNotValid:
			self.assertItemsEqual( Service.objects.all(), [self.service] )