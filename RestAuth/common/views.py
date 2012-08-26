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

from django.views.generic.base import View


class RestAuthView(View):
    """
    Base view for all RestAuth related views.
    """

    def sanitize_arguments(self, resource_name, **kwargs):
        """
        Lowercases kwargs[resource_name] and also add that to kwargs['largs'].
        """
        if 'largs' not in kwargs:
            kwargs['largs'] = {}

        kwargs[resource_name] = kwargs.get(resource_name).lower()
        kwargs['largs'][resource_name] = kwargs.get(resource_name)
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        """
        Adds the 'service' logging argument, and passes that as extra
        keyword-argument to the parents dispatch method.
        """
        largs = kwargs.pop('largs', {})
        largs['service'] = request.user.username
        return super(RestAuthView, self).dispatch(
            request, *args, largs=largs, **kwargs)

class RestAuthResourceView(RestAuthView):
    """
    Class for all views that have one variable in the path, i.e.
    ``/users/<user>/props/``.
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Adds the 'name' logging argument, and passes that as extra
        keyword-argument to the parents dispatch method.
        """
        kwargs = self.sanitize_arguments('name', **kwargs)
        return super(RestAuthResourceView, self).dispatch(
            request, *args, **kwargs)

class RestAuthSubResourceView(RestAuthView):
    """
    Class for all views that have two variables in the path, i.e.
    ``/users/<user>/props/<prop>/``.
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Adds the 'subname' logging argument, and passes that as extra
        keyword-argument to the parents dispatch method.
        """
        kwargs = self.sanitize_arguments('subname', **kwargs)
        return super(RestAuthSubResourceView, self).dispatch(
            request, *args, **kwargs)
