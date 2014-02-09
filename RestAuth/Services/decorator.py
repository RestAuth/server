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

from __future__ import unicode_literals

import logging

from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.conf import settings

log = logging.getLogger(__name__)


def get_auth_challenge(realm):
    response = HttpResponse("Please authenticate", status=401)
    response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
    return response


def login_user(view, request, realm, *args, **kwargs):
    """
    The function called when the login_user decorator is used.
    """
    user = None
    if 'HTTP_AUTHORIZATION' in request.META:
        # The web-server does *not* handle authentication and the client
        # tries to authenticate.
        header = request.META['HTTP_AUTHORIZATION']
        host = request.META['REMOTE_ADDR']
        user = authenticate(header=header, host=host)
    elif 'REMOTE_USER' in request.META:
        # The web-server already authenticated the remote user:
        user = authenticate(remote_user=request.META['REMOTE_USER'])
    elif hasattr(request, 'user') and \
            request.user.is_authenticated():  # pragma: no cover
        return view(request, *args, **kwargs)
    else:
        log.warning("Unable to get authentication source.")
        return get_auth_challenge(realm)

    if user:
        middleware = 'django.contrib.auth.middleware.AuthenticationMiddleware'

        # log the user in:
        if middleware in settings.MIDDLEWARE_CLASSES:  # pragma: no cover
            login(request, user)
        else:
            setattr(request, 'user', user)
        return view(request, *args, **kwargs)
    else:
        # send an authentication challenge:
        log.warning("Client provided wrong authentication credentials")
        return get_auth_challenge(realm)


def login_required(function=None, realm=""):
    """
    Define our own login_required decorator to handle basic authentication,
    performed either by the webserver or the decorator itself.
    """
    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return login_user(func, request, realm, *args, **kwargs)
        return wrapper
    return view_decorator
