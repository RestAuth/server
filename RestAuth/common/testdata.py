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

import base64, httplib, logging

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.client import Client
from django.conf import settings

import RestAuthCommon

from RestAuth.Services.models import Service, service_create
from RestAuth.Users.models import ServiceUser, user_create
from RestAuth.common.middleware import ExceptionMiddleware

username1 = u"mati \u6111"
username2 = u"mati \u6112"
username3 = u"mati \u6113"
username4 = u"mati \u6114"
username5 = u"mati \u6115"

password1 = u"password \u6121"
password2 = u"password \u6122"
password3 = u"password \u6123"
password4 = u"password \u6124"
password5 = u"password \u6125"

groupname1 = u"group 1 \u6131"
groupname2 = u"group 2 \u6132"
groupname3 = u"group 3 \u6133"
groupname4 = u"group 4 \u6134"
groupname5 = u"group 5 \u6135"
groupname6 = u"group 6 \u6136"
groupname7 = u"group 7 \u6137"
groupname8 = u"group 8 \u6138"
groupname9 = u"group 9 \u6139"

propkey1 = u"propkey \u6141"
propkey2 = u"propkey \u6142"
propkey3 = u"propkey \u6143"
propkey4 = u"propkey \u6144"
propkey5 = u"propkey \u6145"

propval1 = u"propval \u6151"
propval2 = u"propval \u6152"
propval3 = u"propval \u6153"
propval4 = u"propval \u6154"
propval5 = u"propval \u6155"


class RestAuthTest( TestCase ):
    def setUp(self):
        if hasattr( self, 'settings' ): # requires django-1.3.1:
            self.settings( LOGGING_CONFIG=None )
        
        self.c = Client()
        self.handler = RestAuthCommon.handlers.json()
        self.extra = {
            'HTTP_ACCEPT': self.handler.mime,
            'REMOTE_USER': 'vowi',
            'content_type': self.handler.mime,
        }
        service_create( 'vowi', 'vowi', [ '127.0.0.1', '::1' ] )
        
        self.factory = RequestFactory()
        self.content_handler = RestAuthCommon.handlers.json()
        self.authorization = "Basic %s"%(base64.b64encode( "vowi:vowi".encode() ).decode() )
        
    def tearDown( self ):
        Service.objects.all().delete()
    
    def request( self, method, url, **kwargs ):
        logging.error( 'This function is deprecated!' )
        request = getattr( self.factory, method )( url, **kwargs )
        request.META['HTTP_AUTHORIZATION'] = self.authorization
        request.META['HTTP_ACCEPT'] = self.content_handler.mime
        return request
    
    def get( self, url, data={} ):
        kwargs = {'data': data}
        request = self.request( 'get', url, **kwargs )
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