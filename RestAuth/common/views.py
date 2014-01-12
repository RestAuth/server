# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not,
# see <http://www.gnu.org/licenses/>.

"""
This module implements common baseclasses used in other RestAuth views..
"""

from __future__ import unicode_literals

from django.views.generic.base import View

from common.types import assert_format
from common.types import parse_dict


class RestAuthView(View):
    """Base view for all RestAuth related views."""

    def _parse_post(self, request):
        data = parse_dict(request)
        return assert_format(data=data, required=getattr(self, 'post_required'),
                             optional=getattr(self, 'post_optional', None))

    def _parse_put(self, request):
        data = parse_dict(request)
        return assert_format(data=data, required=getattr(self, 'put_required', None),
                             optional=getattr(self, 'put_optional', None))

    def dispatch(self, request, **kwargs):
        """
        Adds the 'service' logging argument, and passes that as extra
        keyword-argument to the parents dispatch method.
        """
        largs = kwargs.pop('largs', {})
        largs['service'] = request.user.username

        return super(RestAuthView, self).dispatch(request, largs=largs, **kwargs)


class RestAuthResourceView(RestAuthView):
    """Class for all views that have one variable in the path, i.e. ``/users/<user>/props/``.
    """

    def dispatch(self, request, name, **kwargs):
        """
        Adds the 'name' logging argument, and passes that as extra keyword-argument to the parents
        dispatch method.
        """
        name = name.lower()
        largs = {'name': name}

        return super(RestAuthResourceView, self).dispatch(
            request, largs=largs, name=name, **kwargs)


class RestAuthSubResourceView(RestAuthView):
    """
    Class for all views that have two variables in the path, i.e.
    ``/users/<user>/props/<prop>/``.
    """

    def dispatch(self, request, name, subname, **kwargs):
        """
        Adds the 'subname' logging argument, and passes that as extra keyword-argument to the
        parents dispatch method.
        """
        name = name.lower()
        subname = subname.lower()
        largs = {'name': name, 'subname': subname}

        return super(RestAuthSubResourceView, self).dispatch(
            request, largs=largs, name=name, subname=subname, **kwargs)
