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

from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import importlib

HANDLERS = None
PREFERRED_HANDLER = None
SUPPORTED_HANDLERS = None


def load_handlers():
    global HANDLERS
    global PREFERRED_HANDLER
    global SUPPORTED_HANDLERS

    handlers = []
    for backend in settings.CONTENT_HANDLERS:
        try:
            mod_path, cls_name = backend.rsplit('.', 1)
            mod = importlib.import_module(mod_path)
            handler_cls = getattr(mod, cls_name)
        except (AttributeError, ImportError, ValueError):
            raise ImproperlyConfigured("Handler not found: %s" % backend)

        handler = handler_cls()
        if not getattr(handler, 'mime'):  # pragma: no cover
            raise ImproperlyConfigured("Handler doesn't specify a MIME type: %s" % backend)
        handlers.append(handler)

    HANDLERS = dict([(h.mime, h) for h in handlers])
    PREFERRED_HANDLER = handlers[0]
    SUPPORTED_HANDLERS = HANDLERS.keys()


def get_handler(mimetype=None):
    if PREFERRED_HANDLER is None or HANDLERS is None:  # pragma: no cover
        # just a safety guard, get_supported() below is alwasy called first.
        load_handlers()

    if mimetype is None:
        return PREFERRED_HANDLER
    else:
        try:
            return HANDLERS[mimetype]
        except KeyError:
            raise ValueError(
                "Unknown mimetype %s. Specify a handler in the CONTENT_HANDLERS setting." %
                mimetype)


def get_supported():
    if SUPPORTED_HANDLERS is None:
        load_handlers()
    return SUPPORTED_HANDLERS
