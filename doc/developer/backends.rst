Custom backends
---------------

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

Use RestAuth to hash passwords
______________________________

If your backend has no facilities to hash passwords on its own, you should
definetly use the hash functions used by Django/RestAuth itself when processing
passwords. Django provides two simple functions, ``check_password()`` and
``make_password()`` that you can use.

Simply use those functions in your implementations of
:py:func:`UserBackend.create() <RestAuth.backends.base.UserBackend.create>`,
:py:func:`UserBackend.set_password()
<RestAuth.backends.base.UserBackend.create>` and
:py:func:`UserBackend.check_password()
<RestAuth.backends.base.UserBackend.create>`. Here is a small example:

.. code-block:: python

   from django.contrib.auth.hashers import check_password, make_password

   from RestAuth.backends.base import UserBackend


   class CustomUserBackend(UserBackend):
       def create(self, username, password=None, properties=None,
                  property_backend=None, dry=False, transaction=True):
           # generate hashed password:
           hashed_passsword = make_password(password)

           # save user with hashed password...

       def set_password(self, username, password):
           # generate hashed password:
           hashed_passsword = make_password(password)

           # ... save hashed password for user

       def check_password(self, username, password):
           """Checks password, also updates hash if using an old algorithm."""
           # get password hash from user...
           stored_pwdhash = ...

           def setter(raw_password):
               self.set_password(username, raw_password)
           return check_password(raw_password, stored_pwdhash, setter)


Returning User/Group objects
____________________________

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
