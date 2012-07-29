import random

from django.conf import settings


class MasterSlave(object):
    """
    This router assumes that you have a single master (that can
    perform write operations) and multiple slaves that perform read operations.

    Read operations will be redirected to a random database (including the
    master) and write operations will be directed to the "default" database,
    which should be the master.
    """
    def db_for_read(self, model, **hints):
        choices = settings.DATABASES.keys()
        return random.choice(choices)


class MultipleMasterSlave(object):
    """
    This router handles multiple (read/write) masters and (read-only) slaves.

    Read operations will be redirected to a random database (including any
    masters). Write-operations will be redirected to a random database with a
    designation starting with 'master'.

    Example:

    .. code-block:: python

       DATABASES = {
            'master-a': { ... }, # will get write operations
            'master-b': { ... }, # will get write operations
            'slave': { ... }, # this is a read-only slave
       }

    """
    def db_for_read(self, model, **hints):
        choices = settings.DATABASES.keys()
        return random.choice(choices)

    def db_for_write(self, model, **hints):
        databases = settings.DATABASES.keys()
        choices = [db for db in databases if db.startswith('master')]
        return random.choice(choices)
