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

from django.http import HttpResponse as HttpResponse

from common.types import get_response_type
from common.content_handlers import get_handler


class HttpRestAuthResponse(HttpResponse):
    def __init__(self, request, response_object, status=200):
        mime_type = get_response_type(request)
        handler = get_handler(mime_type)
        body = handler.marshal(response_object)

        HttpResponse.__init__(self, body, mime_type, status, mime_type)


class HttpResponseNoContent(HttpResponse):
    status_code = 204


class HttpResponseCreated(HttpResponse):
    status_code = 201
