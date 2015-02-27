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

from __future__ import unicode_literals, absolute_import

from collections import deque

from django.conf import settings
from django.utils.module_loading import import_string

from common.utils import import_path


def get_group_backend():
    return import_path(getattr(
        settings, 'GROUP_BACKEND',
        'backends.django.DjangoGroupBackend'
    ))[0]()


def get_backend():
    config = getattr(settings, 'DATA_BACKEND', {
        'BACKEND': 'backends.django.DjangoBackend',
    }).copy()
    backend_cls = import_string(config.pop('BACKEND', 'backends.django.DjangoBackend'))
    return backend_cls(**config)

backend = get_backend()
group_backend = get_group_backend()
