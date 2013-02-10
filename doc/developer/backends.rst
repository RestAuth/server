Custom backends
===============

RestAuth :doc:`/config/backends` are written in a way that you can easily write
a drop-in replacement, if you want to use a different storage system for users,
groups or user properties.

To develop your own backend, simply implement one or all of the base classes
below.

.. autoclass:: RestAuth.backends.base.UserBackend
   :members:

.. autoclass:: RestAuth.backends.base.PropertyBackend
   :members:

.. autoclass:: RestAuth.backends.base.GroupBackend
   :members:

Returning User/Group objects
++++++++++++++++++++++++++++

Some backend methods to implement expect (or return) a user/group object. The
objects don't have to be of any particular class but must have a few properties
available. The classes below are given for convenience only, if your objects
already provide the correct properties, there is no need to use them.

In most cases, backends are called similar to this:

.. code-block:: python

   user = user_backend.get(username='some username')
   group = group_backend.get(name='group', service=service)

   group_backend.add_user(group=group, user=user)

Note that in the above case, users and groups may be stored in totally different
backends.

.. autoclass:: RestAuth.backends.base.UserInstance
.. autoclass:: RestAuth.backends.base.GroupInstance
