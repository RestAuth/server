# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.http import HttpResponse as HttpResponseBase

from common.types import get_response_type
from common.content_handlers import get_handler


class HttpRestAuthResponse(HttpResponseBase):
    def __init__(self, request, response_object, status=200):
        mime_type = get_response_type(request)
        handler = get_handler(mime_type)
        body = handler.marshal(response_object)

        HttpResponseBase.__init__(self, body, mime_type, status, mime_type)


class HttpResponseNoContent(HttpRestAuthResponse):
    def __init__(self):
        HttpResponseBase.__init__(self, status=204)


class HttpResponseCreated(HttpRestAuthResponse):
    def __init__(self, request, viewname, **kwargs):
        location = reverse(viewname, kwargs=kwargs)
        uri = request.build_absolute_uri(location)

        HttpRestAuthResponse.__init__(self, request, [uri], 201)
        self['Location'] = uri
