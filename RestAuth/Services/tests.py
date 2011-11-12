import base64, httplib

from django.conf import settings
from django.test.client import RequestFactory

import RestAuthCommon

from RestAuth.common import errors
from RestAuth.common.testdata import RestAuthTest
from RestAuth.Services.models import Service, service_create
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