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

import base64

from django.conf import settings
from django.core.cache import cache
from django.utils import six

from Services.models import Service


class InternalAuthenticationBackend:
    supports_anonymous_user = False
    supports_object_permissions = False

    def _decode3(self, data):  # pragma: py3
        data = base64.b64decode(data)
        return data.decode('utf-8').split(':', 1)

    def _decode2(self, data):  # pragma: py2
        data = base64.b64decode(data)
        return data.split(':', 1)

    def authenticate(self, header, host):
        """
        Authenticate against a header as send by HTTP basic
        authentication and a host. This method takes care of decoding
        the header.

        .. NOTE:: We return None as soon as any check fails in order to avoid
           any accidental pass-through to other parts of the authentication.
        """
        method, data = header.split()
        if method.lower() != 'basic':
            return None  # we only support basic authentication

        qs = Service.objects.only('username', 'password')

        if settings.SECURE_CACHE:
            cache_key = 'service_%s' % data
            cache_data = cache.get(cache_key)

            if cache_data is None:
                try:
                    name, password = self._decode(data)
                except:
                    return None

                try:
                    serv = qs.get(username=name)
                except Service.DoesNotExist:
                    return None

                if serv.check_password(password):
                    # get hosts, store data in cache:
                    hosts = serv.hosts.values_list('address', flat=True)
                    cache.set(cache_key, (serv, hosts))

                    if host in hosts:
                        return serv
                    else:
                        return None
                else:
                    return None
            else:
                serv, hosts = cache_data
                if host in hosts:
                    return serv
                else:
                    return None
        else:
            try:
                name, password = self._decode(data)
            except:
                return None

            try:
                serv = qs.get(username=name)
                if serv.verify(password, host):
                    # service successfully verified
                    return serv
                else:
                    return None
            except Service.DoesNotExist:
                # service does not exist
                return None

    def get_user(self, user_id):  # pragma: no cover
        """
        Get the user by id. This is used by clients that implement
        sessions.
        """
        return Service.objects.get(id=user_id)

    if six.PY3:  # pragma: py3
        _decode = _decode3
    else:  # pragma: py2
        _decode = _decode2
