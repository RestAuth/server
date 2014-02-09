Settings reference
------------------

Since RestAuth is implemented as a Django project, RestAuth not only uses
`all settings available in Django
<https://docs.djangoproject.com/en/dev/ref/settings/>`__, but also features a
few additional settings that ease administration and configure RestAuth. This
document is a complete reference of settings that are either specific to
RestAuth or are normal Django settings that RestAuth handles in a different way.

.. only:: homepage

   .. _dist-specific-file-settings:

   Location of |file-settings-as-file|
   ===================================

   The file |file-settings-as-file| is referenced throughout the documentation.
   The name and location of this file varies depending on how you installed
   RestAuth. Here is an overview of known locations:

   ============================================= ==================================
   Installation method                           Location
   ============================================= ==================================
   :doc:`from source </install/from-source>`     RestAuth/RestAuth/localsettings.py
   :doc:`Debian/Ubuntu </install/debian-ubuntu>` /etc/restauth/settings.py
   :doc:`Fedora </install/redhat-fedora>`        Unknown
   :doc:`Archlinux </install/archlinux>`         Unknown
   ============================================= ==================================

   .. TODO:: Research locations on Fedora and Archlinux

.. NOTE:: If you start digging deeper into RestAuth and Django configuration,
   you will notice, that many configuration variables
   `normally present in a Django settings file
   <https://docs.djangoproject.com/en/dev/topics/settings/>`_ are missing from
   that file. This is because the file is only included in the
   real :file:`settings.py` file. This is why you can set any Django setting in
   your |file-settings-as-file| and overwrite any existing Django setting.

.. setting:: CACHES

CACHES
======

Default: ``see Django documentation``

This setting is `available in Django
<https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-CACHES>`__.  Please see the
`official documentation <https://docs.djangoproject.com/en/dev/topics/cache/>`_ on how to use this
setting.

.. WARNING:: If you change this setting, please also see :setting:`SECURE_CACHE`.

.. setting:: CONTENT_HANDLERS

CONTENT_HANDLERS
================

Default::

   (
      'RestAuthCommon.handlers.JSONContentHandler',
      'RestAuthCommon.handlers.FormContentHandler',
      'RestAuthCommon.handlers.PickleContentHandler',
      'RestAuthCommon.handlers.YAMLContentHandler',
   )

.. versionadded:: 0.6.1

The handlers used to encode/decode content. If you write custom content
handlers, add them here.


.. setting:: GROUP_BACKEND

GROUP_BACKEND
=============

.. versionadded:: 0.6.1

Default: ``'backends.django_backend.DjangoGroupBackend'``

The backend to use to store groups. Please see :ref:`group-backends` for a more
comprehensive description of available backends.  The default is the only
backend shipping with RestAuth, but other backends may be available elsewhere.

If you need a custom backend to store groups, please see
:doc:`/developer/backends`.


.. setting:: GROUP_RECURSION_DEPTH

GROUP_RECURSION_DEPTH
=====================

.. versionadded:: 0.6.0
   In version 0.5.3 and earlier the recursion depth was hard-coded to 10.

Default: ``3``

When calculating group memberships RestAuth supports *nested groups*, where a
group may have parent groups and inherit additional memberships from its parent
groups.

.. NOTE:: Parent groups do not have to belong to the same service if you
   configure them using |bin-restauth-group|. This lets you, for example,
   configure an administration service that can define memberships for its own
   groups and other, lesser privileged services, automatically inherit
   memberships from the groups of the administration service.

A :setting:`GROUP_RECURSION_DEPTH` of 3 means that RestAuth will check 3 levels
of parent groups. Take this example, where ``Group A`` is a parent group of
``Group B`` and so on::

   Group A
   |- Group B
     |- Group C
        |- Group D
           |- Group E

If a user is a member of ``Group A``, he will also be considered a member of
``Group B``, ``Group C`` and ``Group D`` but no longer a member of ``Group E``,
because the third level of parent-groups above is ``Group B``, where the user is
not a "direct" member.

Setting :setting:`GROUP_RECURSION_DEPTH` to ``0`` will disable nested groups
entirely.

.. WARNING:: Do not set this setting to a value greater then necessary. Checking
   nested groups is relatively performance intensive. Set this setting to a
   value as low as possible.

.. setting:: LOGGING

LOGGING
=======

Default: please see source-code

This setting is `available in Django
<https://docs.djangoproject.com/en/dev/ref/settings/#logging>`_. RestAuth has
(unlike Django) an extensive default. Various views assume the presence of
configured loggers, so it is not recommended to change this setting yourself.
If you really know what you are doing, read the real :file:`settings.py` on how
to imitate the required loggers.

.. setting:: LOG_HANDLER

LOG_HANDLER
===========

Default: ``'logging.StreamHandler'``

You can define a different destination of any log messages using
:setting:`LOG_HANDLER`. The setting should be a string containing the classname
of any available handler. See `logging.handlers
<http://docs.python.org/library/logging.handlers.html>`_ for whats available. Of
course nothing stops you from implementing your own handler.

.. setting:: LOG_HANDLER_KWARGS

LOG_HANDLER_KWARGS
==================

Default: ``{}``

Any additional keyword arguments the log handler defined in
:setting:`LOG_HANDLER` LoggingHandler will get.

Here is an example for a `SocketHandler
<http://docs.python.org/library/logging.handlers.html#sockethandler>`_:

.. code-block:: python

   LOG_HANDLER_KWARGS = { 'host': 'localhost', 'port': 10000 }

.. setting:: LOG_LEVEL

LOG_LEVEL
=========

Default: ``'ERROR'``

The default log-level to use. Available values are:

============= =================================================================
Level         Description
============= =================================================================
``CRITICAL``  Only log errors due to an internal malfunction.
``ERROR``     Also log errors due to misbehaving clients.
``WARNING``   Also log requests where an implicit assumption doesn't hold.
              (i.e. when a client assumes that a user exists that in fact does
              not)
``INFO``      Also log successfully processed requests that change data.
``DEBUG``     Also log idempotent requests, i.e. if a user exists, etc.
============= =================================================================

.. setting:: MAX_USERNAME_LENGTH

MAX_USERNAME_LENGTH
===================

Default: ``255``

The maximum length of new usernames. Note that this setting might have any
effect if a validator restricts the maximum length even further.


.. setting:: MIDDLEWARE_CLASSES

MIDDLEWARE_CLASSES
==================

Default::

   (
       'django.middleware.common.CommonMiddleware',
       'common.middleware.RestAuthMiddleware',
   )

RestAuth uses `middlewares
<https://docs.djangoproject.com/en/dev/topics/http/middleware/>`_ like any other
Django project. The default however only contains the bare minimum of required
middlewares.

.. setting:: MIN_PASSWORD_LENGTH

MIN_PASSWORD_LENGTH
===================

Default: ``6``

The minimum length for new passwords. This of course only affects new passwords.

.. setting:: MIN_USERNAME_LENGTH

MIN_USERNAME_LENGTH
===================

Default: ``3``

The minimum length of new usernames. Note that this setting might have any
effect if a validator restricts the minimum length even further.

.. setting:: PASSWORD_HASHERS

PASSWORD_HASHERS
================

.. versionadded:: 0.6.1
   This standard Django setting now replaces the old ``HASH_FUNCTIONS`` and
   ``HASH_ALGORITHMS`` settings. Please see the :ref:`upgrade notes for 0.6.1
   <update_settings_0.6.1>` for more information.

Default::

   PASSWORD_HASHERS = (
       'django.contrib.auth.hashers.PBKDF2PasswordHasher',
       'common.hashers.Sha512Hasher',
       'common.hashers.MediaWikiHasher',
       'common.hashers.Apr1Hasher',
       'common.hashers.Drupal7Hasher',
       'common.hashers.PhpassHasher',
       'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
       'django.contrib.auth.hashers.BCryptPasswordHasher',
       'django.contrib.auth.hashers.SHA1PasswordHasher',
       'django.contrib.auth.hashers.MD5PasswordHasher',
       'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
       'django.contrib.auth.hashers.CryptPasswordHasher',
   )

RestAuth can store password hashes in different formats. RestAuth ships with
additional hashers for MediaWiki, Apr1 (Apache .htaccess files) and SHA-512
hashes. Thanks to these hashers, RestAuth understands and can even create hashes
as used by the respective systems.

If you need to import hashes from a different system, you can easily write your
own password hasher. Please see :doc:`/config/custom-hashes` for more
information.

.. NOTE:: This setting is by default also used for services. You can speed up
   RestAuth with the :setting:`SERVICE_PASSWORD_HASHER` setting.

.. setting:: PROPERTY_BACKEND

PROPERTY_BACKEND
================

.. versionadded:: 0.6.1

Default: ``'backends.django_backend.DjangoPropertyBackend'``

The backend to use to store user properties. RestAuth comes with two property
backends:

``'backends.django_backend.DjangoPropertyBackend'``
   Use the standard Django ORM to store property data. This backend requireds
   that you also use the DjangoUserBackend.

``'backends.redis_backend.RedisPropertyBackend'``
   Use a `Redis <http://redis.io>`_ server to store properties.

Please see :ref:`property-backends` for a more comprehensive description of
available backends. Other backends may be available elsewhere, if you need to
develop your own backend, please see :doc:`/developer/backends`.

.. setting:: RELAXED_LINUX_CHECKS

RELAXED_LINUX_CHECKS
====================

Default: ``False``

When this variable is set to ``True``, the validator will apply a more relaxed
check. Please see the :py:class:`linux validator <.linux>` for more information.

.. setting:: SECRET_KEY

SECRET_KEY
==========

Never forget to set a `SECRET_KEY
<https://docs.djangoproject.com/en/dev/ref/settings/#secret-key>`_ in
|file-settings-link|.

.. setting:: SECURE_CACHE

SECURE_CACHE
============

.. versionadded:: 0.6.1
.. versionchanged:: 0.6.4
   The default is now ``True``, it used to be ``False`` previously.

Default: ``True``

By default, RestAuth caches service credentials. This is fine with the default settings, since
Django by default uses an in-memory cache (see :setting:`CACHES`) and once an attacker is able to
read in-memory datastructures, all information protected by the credentials are already compromised
anyway.

Depending on other settings, you might want to set this to ``False``:

* If you use a different caching backend, i.e. memcached or redis.
* If you use a cache on another host, it is highly recommended to set this to ``False``.
* If you want to make it as unlikely as possible for an attacker to get service credentials on an
  already compromised RestAuth server.

.. setting:: SERVICE_PASSWORD_HASHER

SERVICE_PASSWORD_HASHER
=======================

.. versionadded:: 0.6.1

default: ``default``

You may override the hasher used for hashing service passwords. Since the
passwords used for service authentication are usually not very valuable
(auto-generated, easily changeable) you may choose a faster hashing
algorithm from any algorithm found in :setting:`PASSWORD_HASHERS`. The special
value ``default`` (which is the default) means the first hasher in
:setting:`PASSWORD_HASHERS`.  This speeds up RestAuth significantly, but has the
security drawback that an attacker might be able to retrieve service
credentials from the cache..

.. setting:: USER_BACKEND

USER_BACKEND
============

.. versionadded:: 0.6.1

Default: ``'backends.django_backend.UserBackend'``

The backend used for storing user data. Please see :ref:`user-backends` for a
more comprehensive description of available backends. The default is the only
backend shipping with RestAuth, but other backends may be available elsewhere.

If you need a custom backend to store user data, please see
:doc:`/developer/backends`.

.. setting:: VALIDATORS

VALIDATORS
==========

.. versionadded:: 0.5.3
   In version 0.5.2 and earlier ``SKIP_VALIDATORS`` configured roughly the
   inverse. Please see the :ref:`upgrade notes <update_settings_0.5.3>` if you
   still use the old setting.

Default: ``[]``

By default, usernames in RestAuth can contain any UTF-8 character except a slash
('/'), a backslash ('\\') and a colon (':'). You can add additional validators
to restrict usernames further to ensure that new usernames are compatible with
all systems you use.

.. NOTE:: Validators are only used when creating new accounts. This way existing
   users can still login to existing systems if you enable additional validators
   later on, even if their username is illegal in a new system.

Example configuration for disabling the registration of accounts incompatible
with either MediaWiki or XMPP:

.. code-block:: python

   VALIDATORS = [
       'Users.validators.mediawiki',
       'Users.validators.xmpp',
   ]

Please see :doc:`/config/username-validation` for information on what validators
exist and how to write your own validators.
