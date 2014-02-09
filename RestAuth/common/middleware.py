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

"""
The ExceptionMiddleware is located in its own class to avoid circular imports.
"""

from __future__ import unicode_literals

import logging
import traceback

from django.http import HttpResponse

from RestAuthCommon.error import RestAuthException

from common.errors import GroupNotFound
from common.errors import PropertyNotFound
from common.errors import UserNotFound

log = logging.getLogger(__name__)
CONTENT_TYPE_METHODS = set(['POST', 'PUT'])


class RestAuthMiddleware:
    def process_request(self, request):
        """Middleware to ensure required headers are present."""

        if request.method in CONTENT_TYPE_METHODS:
            if 'CONTENT_TYPE' not in request.META:
                return HttpResponse(
                    'POST/PUT requests must include a Content-Type header.',
                    status=415
                )

        if 'HTTP_ACCEPT' not in request.META:  # pragma: no cover
            log.warning('Accept header is recommended in all requests.')

    def process_exception(self, request, ex):
        """Handle RestAuth related exceptions."""

        if isinstance(ex, UserNotFound):
            resp = HttpResponse(ex, status=404)
            resp['Resource-Type'] = 'user'
            return resp
        elif isinstance(ex, GroupNotFound):
            resp = HttpResponse(ex, status=404)
            resp['Resource-Type'] = 'group'
            return resp
        elif isinstance(ex, PropertyNotFound):
            resp = HttpResponse(ex, status=404)
            resp['Resource-Type'] = 'property'
            return resp
        elif isinstance(ex, AssertionError):
            return HttpResponse(' '.join(ex.args), status=400)
        elif isinstance(ex, RestAuthException):
            return HttpResponse(' '.join(ex.args), status=ex.response_code)
        else:  # pragma: no cover
            log.critical(traceback.format_exc())
