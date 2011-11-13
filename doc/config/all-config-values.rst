Settings
--------

Since RestAuth is implemented as a Django project, RestAuth not only uses all `settings available in
Django <https://docs.djangoproject.com/en/dev/ref/settings/>`_, but also features a few additional
settings that ease administration and configure RestAuth. This document is a complete reference of
settings that are either specific to RestAuth or are normal Django settings that RestAuth handles
in a different way.

.. setting:: CACHES

CACHES
======

Default: ``{}``

This setting is `available in Django
<https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-CACHES>`_. Please see the `official
documentation <https://docs.djangoproject.com/en/dev/topics/cache/>`_ on how to use this setting.

RestAuth automatically adjusts :setting:`MIDDLEWARE_CLASSES` (as documented `here
<https://docs.djangoproject.com/en/dev/topics/cache/#the-per-site-cache>`_) if you configure any
caches.

.. setting:: ENABLE_SESSIONS

ENABLE_SESSIONS
===============

Default: ``False``

The RestAuth protocol by default does not use HTTP sessions, since every request is authenticated
using HTTP Basic Authentication. Sessions are thus disabled in RestAuth, because they come with a
considerable performance penalty.

If a client still uses HTTP sessions, you can set this configuarion variable to ``True``. This has
the effect of adding the appropriate middleware classes to :setting:`MIDDLEWARE_CLASSES`.

.. setting:: FILTER_LINUX_USERNAME_NOT_RECOMMENDED

FILTER_LINUX_USERNAME_NOT_RECOMMENDED
=====================================

Default: ``True``

Linux allows virtually any username, but does not recommend usernames that:

* do not start with a lowercase letter or an underscore ('_')
* consist only of lowercase letters, digits, underscores ('_') or dashes ('-')

Setting this variable to False causes the ``linux`` validator (see :setting:`SKIP_VALIDATORS`) to
only apply a more relaxed check. Even when set to ``False``, usernames can only be 32 characters
long, may not start with a dash ('-') and may not contain any whitespace character.

.. setting:: HASH_ALGORITHM

HASH_ALGORITHM
==============

Default: ``sha512``

The :setting:`HASH_ALGORITHM` setting configures which algorithm is used for hashing new passwords.
If you set this to a new algorithm, old password hashes will be updated whenever a user logs in.
RestAuth supports all algorithms supported by the `hashlib module
<http://docs.python.org/library/hashlib.html>`_.

RestAuth also supports reading and storing hashes the same way that legacy systems store
them. *Reading* such hashes has the advantage of being able to import user databases from those
systems. *Storing* new hashes this way lets you move the password database back to one of those
systems. Currently the only other supported system is ``mediawiki``. 

.. setting:: LOGGING

LOGGING
=======

Default: please see source-code

This setting is `available in Django
<https://docs.djangoproject.com/en/dev/ref/settings/#logging>`_. RestAuth has (unlike Django) an
extensive default. Various views assume the presence of configured loggers, so it is not recommended
to change this setting yourself. If you really know what you are doing, read :file:`settings.py`
on how to imitate the required loggers.

.. setting:: LOG_HANDLER

LOG_HANDLER
===========

Default: ``'logging.StreamHandler'``

You can define a different destination of any log messages using :setting:`LOG_HANDLER`. The setting
should be a string containing the classname of any available handler. See `logging.handlers
<http://docs.python.org/library/logging.handlers.html>`_ for whats available. Of course nothing
stops you from implementing your own handler.

.. setting:: LOG_HANDLER_KWARGS

LOG_HANDLER_KWARGS
==================

Default: ``{}``

Any additional keyword arguments the log handler defined in :setting:`LOG_HANDLER` LoggingHandler
will get.
  
Here is an example for a `SocketHandler
<http://docs.python.org/library/logging.handlers.html#sockethandler>`_:

.. code-block:: python

   LOG_HANDLER_KWARGS = { 'host': 'localhost', 'port': 10000 }

.. setting:: LOG_LEVEL

LOG_LEVEL
=========

Default: ``'ERROR'``

The default log-level to use. Available values are:

============= =====================================================================
Level         Description
============= =====================================================================
``CRITICAL``  Only log errors due to an internal malfunction.
``ERROR``     Also log errors due to misbehaving clients.
``WARNING``   Also log requests where an implicit assumption doesn't hold.
              (i.e. when a client assumes that a user exists that in fact does not)
``INFO``      Also log successfully processed requests that change data.
``DEBUG``     Also log idempotent requests, i.e. if a user exists, etc.
============= =====================================================================

.. setting:: MAX_USERNAME_LENGTH

MAX_USERNAME_LENGTH
===================

Default: ``255``

The maximum length of new usernames. Note that this setting might have any effect if a validator
restricts the maximum length even further.


.. setting:: MIDDLEWARE_CLASSES

MIDDLEWARE_CLASSES
==================

Default::
   
   ['django.middleware.common.CommonMiddleware',
    'RestAuth.common.middleware.ExceptionMiddleware',
    'RestAuth.common.middleware.HeaderMiddleware',]
    
RestAuth uses `middlewares <https://docs.djangoproject.com/en/dev/topics/http/middleware/>`_ like
any other Django project. The default however only contains the bare minimum of required
middlewares. Various settings (currently :setting:`CACHES` and :setting:`ENABLE_SESSIONS`) influence
the effective value of this setting.

Additionally, :setting:`MIDDLEWARE_CLASSES` is a list and not a tuple. This allows you to add your
own middleware at any position without having to reconfigure the entire setting. If you do, please
consult :setting:`CACHES` and :setting:`ENABLE_SESSIONS` to see how they manipulate
:setting:`MIDDLEWARE_CLASSES` to get the effective value. 
    
.. setting:: MIN_PASSWORD_LENGTH

MIN_PASSWORD_LENGTH
===================

Default: ``6``

The minimum length for new passwords. This of course only affects new passwords.

.. setting:: MIN_USERNAME_LENGTH

MIN_USERNAME_LENGTH
===================

Default: ``3``

The minimum length of new usernames. Note that this setting might have any effect if a validator
restricts the minimum length even further.

.. setting:: SECRET_KEY

SECRET_KEY
----------

Never forget to set a `SECRET_KEY <https://docs.djangoproject.com/en/dev/ref/settings/#secret-key>`_
in :file:`localsettings.py`.

.. setting:: SKIP_VALIDATORS

SKIP_VALIDATORS
===============

Default: ``[ 'linux', 'windows', 'email', 'xmpp' ]``

What :ref:`validators <config_validators>` to skip to relax the minimum requirements on usernames.

The currently available validators are:

============= ============
validator     restrictions
============= ============
``email``     todo
``linux``     todo
``mediawiki`` todo
``windows``   todo
``xmpp``      todo
============= ============

.. todo:: Provide an ability to add your own validators.