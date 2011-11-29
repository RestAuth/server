Username validation
-------------------

By default, usernames in RestAuth can contain any UTF-8 character except a slash ('/'), a backslash
('\\') and a colon (':'). You can add additional validators using the :setting:`VALIDATORS` setting
to restrict usernames further to ensure that new usernames are compatible with all systems you use.

Validators are only used when creating new accounts. This way existing users can still login to
existing systems if you enable additional validators later on, even if their username is illegal in
a new system.

Which validators to enable (and when)
=====================================

We recommend that you enable as few validators as possible. RestAuth in principle supports almost
any username and has full UTF-8 support. Many validators restrict usernames to ASCII characters and
even there forbid many special characters, some do not allow spaces. Please refer to the
:ref:`available validators <available-validators>` for exact documentation on what validators
restrict which usernames.

On the other hand, make sure that you enable validators for systems you might use in the future
right away. This way users cannot register usernames that will be unusable on any future system.

.. _available-validators:

Available validators
====================

The following validators ship with RestAuth. These validators are implemented to the best knowledge
available, but are of course in no way guaranteed to really catch all illegal usernames. If you
find inconsistencies, please consider to :ref:`contribute <contribute-validators>`.

.. automodule:: RestAuth.Users.validators
   :members: email, mediawiki, linux, windows, xmpp, drupal

Implement your own validators
=============================

You can easily implement your own validators, if you now a little Python. This chapter assumes at
least a little knowledge of Python, but you don't have to be an expert.

To implement a validator, simply inherit from :py:class:`validator` and override any fields or
methods. This is the class you want to inherit from:

.. autoclass:: RestAuth.Users.validators.validator
   :members:

More complex validations
++++++++++++++++++++++++

If the fields in :py:class:`validator` do not cover your needs, you can add a classmethod called
``check`` to implement your own, more complex checks. This method must raise
:py:class:`RestAuth.common.errors.UsernameInvalid` if the check fails.

Example
+++++++

Here is a full example of what a validator might look like. Remember, every single part of this can
be skipped, if you don't need it (and you should, to improve performance).

.. code-block:: python

   from RestAuth.common.validators import validator
   from RestAuth.common.errors import UsernameInvalid
   
   class MyOwnValidator( validator ):
       # The characters 'a', 'f' and '#' are not allowed:
       ILLEGAL_CHARACTERS = set(['a', 'f', '#'])
       
       # We do not allow whitespace (default is True):
       ALLOW_WHITESPACE = False
	
       # We do allow UTF-8 characters (default is True):
       FORCE_ASCII = True
	
       # "user", "admin" and "root" are reserved usernames:
       RESERVED = set(["user", "root", "admin"])
       
       @classmethod
       def check(cls, username):
           """A more advanced check: Usernames must not end with a 'z'."""
	   if username.endswith('z'):
	       raise UsernameInvalid("Usernames must not end with a 'z'")
	       
All you need to do to enable this validator is to put this validator in a .py file somewhere where
the Python interpreter will find it and add the classpath to your :setting:`VALIDATORS`:

.. code-block:: python
   
   VALIDATORS = [ 'some.path.myvalidators.MyOwnValidator' ]

.. _contribute-validators:

Contribute validators
=====================

RestAuth is Free Software and invites everyone to contribute. Validators are a particular easy way
to contribute to RestAuth. You do not even have to provide an implementation, you already provide
great help if you just collect all the information necessary to implement a validator for the given
system.

Please feel free to get in touch with us (see :doc:`contribute </contribute>`) if you need RestAuth
to provide a validator for an additional system.