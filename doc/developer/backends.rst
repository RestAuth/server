Custom backends
---------------

RestAuth :doc:`/config/backends` are written in a way that you can easily write
a drop-in replacement, if you want to use a different storage system for users,
groups or user properties.

To develop your own backend, simply implement the base class below:

.. autoclass:: backends.base.BackendBase
   :members:

Use RestAuth to hash passwords
______________________________

If your backend has no facilities to hash passwords on its own, you should
definetly use the hash functions used by Django/RestAuth itself when processing
passwords. Django provides two simple functions, ``check_password()`` and
``make_password()`` that you can use.

Simply use those functions in your implementations of
:py:func:`~backends.base.BackendBase.create_user`,
:py:func:`~backends.base.BackendBase.set_password` and
:py:func:`~backends.base.BackendBase.check_password`. Here is a small example:

.. code-block:: python

   from django.contrib.auth.hashers import check_password, make_password

   from backends.base import BackendBase


   class CustomBackend(BackendBase):
       def create(self, username, password=None, properties=None, groups=None):
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

Use third-party libraries
_________________________

If you want to use a third-party library for your backend, use the
``_load_library()`` method implemented in ``RestAuthBackend``. All Backend
classes mentioned above inherit from this class.

.. autoclass:: backends.base.BackendBase
   :members:
