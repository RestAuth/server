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

import logging
import sys
import traceback

from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from RestAuthCommon.error import RestAuthException

from RestAuth.Users.models import Property
from RestAuth.Users.models import ServiceUser
from RestAuth.Groups.models import Group

CONTENT_TYPE_METHODS = ['POST', 'PUT']


class ExceptionMiddleware:
    """
    Exception to handle RestAuth related exceptions.
    """
    def process_exception(self, request, ex):
        if isinstance(ex, ServiceUser.DoesNotExist):
            resp = HttpResponse(ex, status=404)
            resp['Resource-Type'] = 'user'
            return resp
        if isinstance(ex, Group.DoesNotExist):
            resp = HttpResponse(ex, status=404)
            resp['Resource-Type'] = 'group'
            return resp
        if isinstance(ex, Property.DoesNotExist):
            resp = HttpResponse(ex, status=404)
            resp['Resource-Type'] = 'property'
            return resp

        if isinstance(ex, RestAuthException):
            return HttpResponse(ex.message, status=ex.response_code)
        else:  # pragma: no cover
            logging.critical(traceback.format_exc())
            return HttpResponseServerError(
                "Internal Server Error. Please see server log for details.\n")


class HeaderMiddleware:
    """
    Middleware to ensure required headers are present.
    """
    def process_request(self, request):
        if request.method in CONTENT_TYPE_METHODS and \
                'CONTENT_TYPE' not in request.META:
            return HttpResponse(
                'POST/PUT requests must include a Content-Type header.',
                status=415
            )

        if 'HTTP_ACCEPT' not in request.META:  # pragma: no cover
            logging.warn('Accept header is recommended in all requests.')
