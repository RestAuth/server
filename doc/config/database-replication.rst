Database replication
====================

Database replication is tricky to set up and maintain. RestAuth provides two `Database routers
<https://docs.djangoproject.com/en/dev/topics/db/multi-db/#automatic-database-routing>`_ that should
help you with the most common replication situations. If you desire more information, please consult
the `Multiple databases chapter
<https://docs.djangoproject.com/en/dev/topics/db/multi-db/#topics-db-multi-db-routing>`_ in the
Django documentation.

.. WARNING:: Only use database routers when you actually use multiple databases. Adding a router
   does introduce a (negligible) performance overhead.

Using database routers
----------------------

To use a database router (you can either :ref:`write your own <config-db-replication-existing>` or
:ref:`use an existing one <config-db-replication-existing>`), simply add it to the
``DATABASE_ROUTERS`` setting in :file:`localsettings.py` (or file:`/etc/restauth/settings.py` on
Debian/Ubuntu). For example, if you want to use our :py:class:`MasterSlave` router, simply add:

.. code-block:: python
   
   DATABASE_ROUTERS = ['RestAuth.common.routers.MasterSlave']
   
.. NOTE:: Routers shipping with RestAuth are not intended to be used together with other routers.
   If you require a more complex database routing schema you can either:
   
   * `File a feature request <https://redmine.fsinf.at/projects/restauth-server/issues/new>`_ if you
     think this is a common scheme that will be used by others, or
   * implement it yourself

.. _config-db-replication-write:

Implementing your own routers
-----------------------------

You can also implement your own router if you require a more complex configuration. Writing routers
is documented in `in the Django documentation
<https://docs.djangoproject.com/en/dev/topics/db/multi-db/#automatic-database-routing>`_ and
requires you to be able to code in Python.

.. _config-db-replication-existing:

Existing database routers
-------------------------
.. automodule:: RestAuth.common.routers
   :members: