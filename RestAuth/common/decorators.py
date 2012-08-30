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

import django
from django.db import connection


def sql_profiler(view, request, *args, **kwargs):  # pragma: no cover
    """
    Wrapper-function for the sql_profile decorator.
    """
    connection.queries = []

    try:
        return view(request, *args, **kwargs)
    finally:
        print('%s queries:' % (len(connection.queries)))
        for query in connection.queries:
            print('%s; (%s secs)' % (query['sql'], query['time']))


def sql_profile(function=None):  # pragma: no cover
    """
    Decorator that lets you profile the sql queries made by a request. This
    isn't used anywhere by default, it is mainly used for debugging.
    """
    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return sql_profiler(func, request, *args, **kwargs)
        return wrapper
    return view_decorator


if django.get_version() >= '1.4':
    from django.test.utils import override_settings
else:  # pragma: no cover
    from functools import wraps

    from django.conf import settings, UserSettingsHolder
    from django.test.signals import setting_changed

    # until class override_settings this is a direct copy of
    #   django/test/signals.py
    # ... from Django 1.4
    from django.db import connections
    from django.dispatch import Signal

    setting_changed = Signal(providing_args=["setting", "value"])

    def update_connections_time_zone(**kwargs):
        if kwargs['setting'] == 'USE_TZ' and settings.TIME_ZONE != 'UTC':
            USE_TZ, TIME_ZONE = kwargs['value'], settings.TIME_ZONE
        elif kwargs['setting'] == 'TIME_ZONE' and not settings.USE_TZ:
            USE_TZ, TIME_ZONE = settings.USE_TZ, kwargs['value']
        else:   # no need to change the database connnections' time zones
            return

        tz = 'UTC' if USE_TZ else TIME_ZONE
        for conn in connections.all():
            tz_sql = conn.ops.set_time_zone_sql()
            if tz_sql:
                conn.cursor().execute(tz_sql, [tz])

    setting_changed.connect(update_connections_time_zone)

    class override_settings(object):
        """
        This class is an exact copy of the decorator introduced in Django 1.4
        and is subject to the same license.

        Acts as either a decorator, or a context manager. If it's a decorator it
        takes a function and returns a wrapped function. If it's a contextmanager
        it's used with the ``with`` statement. In either event entering/exiting
        are called before and after, respectively, the function/block is executed.
        """
        def __init__(self, **kwargs):
            self.options = kwargs
            self.wrapped = settings._wrapped

        def __enter__(self):
            self.enable()

        def __exit__(self, exc_type, exc_value, traceback):
            self.disable()

        def __call__(self, test_func):
            from django.test import TransactionTestCase
            if isinstance(test_func, type) and issubclass(test_func, TransactionTestCase):
                original_pre_setup = test_func._pre_setup
                original_post_teardown = test_func._post_teardown
                def _pre_setup(innerself):
                    self.enable()
                    original_pre_setup(innerself)
                def _post_teardown(innerself):
                    original_post_teardown(innerself)
                    self.disable()
                test_func._pre_setup = _pre_setup
                test_func._post_teardown = _post_teardown
                return test_func
            else:
                @wraps(test_func)
                def inner(*args, **kwargs):
                    with self:
                        return test_func(*args, **kwargs)
            return inner

        def enable(self):
            override = UserSettingsHolder(settings._wrapped)
            for key, new_value in self.options.items():
                setattr(override, key, new_value)
            settings._wrapped = override
            for key, new_value in self.options.items():
                setting_changed.send(sender=settings._wrapped.__class__,
                                     setting=key, value=new_value)

        def disable(self):
            settings._wrapped = self.wrapped
            for key in self.options:
                new_value = getattr(settings, key, None)
                setting_changed.send(sender=settings._wrapped.__class__,
                                     setting=key, value=new_value)

