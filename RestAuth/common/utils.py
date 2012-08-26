from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

def import_path(path):
    try:
        modname, attrname = path.rsplit('.', 1)
    except ValueError:
        raise ImproperlyConfigured('%s isn\'t a middleware module' % path)

    try:
        mod = import_module(modname)
    except ImportError as e:
        raise ImproperlyConfigured(
            'Error importing middleware %s: "%s"' % (modname, e))
    try:
        return getattr(mod, attrname), attrname
    except AttributeError:
        msg = 'Middleware module "%s" does not define a "%s" class'
        raise ImproperlyConfigured(msg % (modname, classname))
