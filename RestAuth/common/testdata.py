
import base64, httplib

from django.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings

import RestAuthCommon

from RestAuth.Services.models import Service, service_create
from RestAuth.Users.models import ServiceUser, user_create
from RestAuth.common.middleware import ExceptionMiddleware

username1 = u"mati \u6110"
username2 = u"mati \u6111"
username3 = u"mati \u6112"
username4 = u"mati \u6110"
username5 = u"mati \u6111"

password1 = u"pass \u6112"
password2 = u"pass \u6113"
password3 = u"pass \u6114"
password4 = u"pass \u6115"
password5 = u"pass \u6116"

group1 = u"group \u6117"
group2 = u"group \u6118"
group3 = u"group \u6119"
group4 = u"group \u6120"
group5 = u"group \u6121"

class RestAuthTest( TestCase ):
    def setUp(self):
        self.factory = RequestFactory()
        self.content_handler = RestAuthCommon.handlers.json()
        self.authorization = "Basic %s"%(base64.b64encode( "vowi:vowi".encode() ).decode() )
        
        service_create( 'vowi', 'vowi', [ '127.0.0.1', '::1' ] )
        
    def tearDown( self ):
        Service.objects.all().delete()
        
    def get_usernames( self ):
        return list( ServiceUser.objects.values_list( 'username', flat=True ) )
    
    def request( self, method, url, **kwargs ):
        request = getattr( self.factory, method )( url, **kwargs )
        request.META['HTTP_AUTHORIZATION'] = self.authorization
        request.META['HTTP_ACCEPT'] = self.content_handler.mime
        return request
    
    def get( self, url ):
        request = self.request( 'get', url )
        return request
    
    def post( self, url, data ):
        post_data = self.content_handler.marshal_dict( data )
        kwargs = { 'data': post_data, 'content_type': self.content_handler.mime }
        request = self.request( 'post', url, **kwargs )
        
        return request
    
    def put( self, url, data ):
        put_data = self.content_handler.marshal_dict( data )
        kwargs = { 'data': put_data, 'content_type': self.content_handler.mime }
        request = self.request( 'put', url, **kwargs )
        
        return request
    
    def delete( self, url ):
        request = self.request( 'delete', url )
        return request
    
    def parse( self, response, typ ):
        body = response.content.decode( 'utf-8' )
        func = getattr( self.content_handler, 'unmarshal_%s'%typ )
        return func( body )
        
    def make_request( self, func, request, *args, **kwargs ):
        try:
            return func( request, *args, **kwargs )
        except Exception as e:
            for middleware in settings.MIDDLEWARE_CLASSES:
                try :
                    path, mod = middleware.rsplit( '.', 1 )
                    module = __import__( path, fromlist=[mod] )
                except ImportError:
                    print( 'import error')
                    
                for string in dir( module ):
                    member = getattr( module, string )
                    if hasattr( member, 'process_exception' ):
                        handler = member()
                        ret = handler.process_exception( request, e )
                        if ret != None:
                            return ret
            raise e