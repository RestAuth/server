Custom password hashes
----------------------

RestAuth understands various hashing algorithms supported by Django, as well as
a few custom hashing algorithms. You can configure the algorithms supported by
RestAuth with the :setting:`PASSWORD_HASHERS` setting. This setting is a
`standard Django setting
<https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-PASSWORD_HASHERS>`_,
but RestAuth supports a few additional hashers by default.

You can :ref:`implement your own hashing algorithm <own-hash-functions>` if you
intend to import data from a system not supported by RestAuth. If your hasher is
the first hasher listed in :setting:`PASSWORD_HASHERS`, RestAuth will also store
hashes using this algorithm. This is useful if you plan to later export data to
such a system.

.. _available-hash-functions:

Available hash functions
========================

RestAuth supports all hashers shipping with Django. RestAuth also already
implements a few other hashers.

.. automodule:: RestAuth.common.hashers
   :members: Apr1Hasher, Drupal7Hasher, MediaWikiHasher, PhpassHasher, Sha512Hasher

.. _own-hash-functions:

Implement your own hash functions
=================================

We use the password hashing mechanisms shipping with Django. If you want to
implement your own hasher, you may want to read up on `how Django stores
passwords
<https://docs.djangoproject.com/en/dev/topics/auth/passwords/#auth-password-storage>`_
first. The official documentation is a little lacking on how to implement your
own hashers, so here are a few additional instructions:

* Your class should inherit from
  ``django.contrib.auth.hashers.BasePasswordHasher``.
* You must implement the ``algorithm`` property as well as the ``verify()``,
  ``encode()`` and ``safe_summery()`` methods.
* If you need to generate salts in a specific way, also implement the ``salt()``
  method.

Here is the documentation for the baseclass shipping with django:

.. autoclass:: django.contrib.auth.hashers.BasePasswordHasher
   :members:

Example
=======

For examples on how to implement your own hashers, please look at the source
code of the very simple :py:class:`RestAuth.common.hashers.Sha512Hasher`.
