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

import mimeparse

from RestAuthCommon.error import BadRequest
from RestAuthCommon.error import NotAcceptable
from RestAuthCommon.error import UnmarshalError
from RestAuthCommon.error import UnsupportedMediaType

from common.content_handlers import get_handler
from common.content_handlers import get_supported


def get_response_type(request):
    supported = get_supported()

    header = request.META['HTTP_ACCEPT']
    match = mimeparse.best_match(supported, header)
    if match:
        return match
    else:
        raise NotAcceptable()


def parse_dict(request):
    supported = get_supported()

    header = request.META['CONTENT_TYPE']
    mime_type = mimeparse.best_match(supported, header)
    if mime_type:
        handler = get_handler(mime_type)

        try:
            data = handler.unmarshal_dict(request.body)
            assert isinstance(data, dict), "Request body is not a dictionary."
            return data
        except UnmarshalError:
            raise BadRequest()
    else:
        raise UnsupportedMediaType()


def assert_format(data, required=None, optional=None):
    retlist = []

    if required is not None:
        for key, typ in required:
            field = data.pop(key, None)
            assert field is not None, 'Required field %s missing.' % key
            assert isinstance(field, typ), \
                    "Required Field %s has wrong type: %s" % (key, type(field))
            retlist.append(field)

    if optional is not None:
        for key, typ in optional:
            field = data.pop(key, None)
            assert isinstance(field, typ) or field is None, \
                "%s is of wrong type: %s" % (key, field)
            retlist.append(field)

    keylist = ', '.join(data.keys())
    assert not data, "Submitted data has unknown keys: %s" % keylist

    if len(retlist) == 1:
        return retlist[0]
    else:
        return retlist
