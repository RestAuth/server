import httplib, base64
from RestAuth.Services.models import Service, service_create
from RestAuth.Users.models import ServiceUser as User
from RestAuth.Users import views
from RestAuth.common.testdata import RestAuthTest, username1, password1
from RestAuth.common.middleware import HeaderMiddleware
import RestAuthCommon

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