import httplib, base64
from RestAuth.Services.models import Service, service_create
from RestAuth.Users.models import ServiceUser as User
from RestAuth.Users import views
from RestAuth.common.testdata import RestAuthTest, username1, password1
from RestAuth.common.middleware import HeaderMiddleware
import RestAuthCommon
from RestAuthCommon.error import UnsupportedMediaType, NotAcceptable

from django.test.client import Client, RequestFactory
from django.utils.unittest import TestCase

class HeaderMiddlewareTests( TestCase ):
    def setUp( self ):
        self.handler = RestAuthCommon.handlers.json()
        self.extra = {
            'HTTP_ACCEPT': self.handler.mime,
            'REMOTE_USER': 'vowi',
            'content_type': self.handler.mime,
        }
        
        self.factory = RequestFactory()
        self.mw = HeaderMiddleware()
        
    def tearDown( self ):
        Service.objects.all().delete()
    
    def test_post_missing_content_type( self ):
        content = self.handler.marshal_dict({'user':username1})
        request = self.factory.post( '/users/', content, **self.extra )
        del request.META['CONTENT_TYPE']
        resp = self.mw.process_request(request)
        self.assertEquals( resp.status_code, httplib.UNSUPPORTED_MEDIA_TYPE )

    def test_put_missing_content_type( self ):
        content = self.handler.marshal_dict({'user':username1})
        request = self.factory.put( '/users/', content, **self.extra )
        del request.META['CONTENT_TYPE']
        resp = self.mw.process_request(request)
        self.assertEquals( resp.status_code, httplib.UNSUPPORTED_MEDIA_TYPE )
        
class ContentTypeTests( RestAuthTest ):
    def setUp( self ):
        RestAuthTest.setUp( self )
        self.factory = RequestFactory()
        
    def test_wrong_content_type_header( self ):
        content = self.handler.marshal_dict( { 'user': username1 } )
        extra = self.extra
        del extra['content_type']
        resp = self.c.post( '/users/', content, content_type='foo/bar', **extra )
        self.assertEquals( resp.status_code, httplib.UNSUPPORTED_MEDIA_TYPE )
        self.assertItemsEqual( User.objects.all(), [] )
    
    def test_wrong_accept_header( self ):
        extra = self.extra
        extra['HTTP_ACCEPT'] = 'foo/bar'
        resp = self.c.get( '/users/', **extra )
        self.assertEquals( resp.status_code, httplib.NOT_ACCEPTABLE )
        self.assertItemsEqual( User.objects.all(), [] )
        
    def test_wrong_content( self ):
        content = 'no_json_at_all}}}'
        resp = self.c.post( '/users/', content,  **self.extra )
        self.assertEquals( resp.status_code, httplib.BAD_REQUEST )
        self.assertItemsEqual( User.objects.all(), [] )