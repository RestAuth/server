Update instructions
-------------------

Updating RestAuth consists of three steps: First you have to update the source
code and database schema. You should also check for new available settings when
a new version becomes available.

Update source
=============

The specific installation instructions for your platform provide documentation
on how to update your source code:

* :ref:`from source <source-update>`
* :ref:`with pip <pip-update>`
* :ref:`Debian/Ubuntu <debian-update>`
* :ref:`Fedora <fedora-update>`
* :ref:`Arch Linux <arch-update>`

.. _update-database:

Update database schema
======================

Starting from version 0.5.3, we use `Django South`_ to handle schema migrations.
If you installed from source, simply use |bin-restauth-manage-link| to update
your schema:

.. parsed-literal:: |bin-restauth-manage| migrate

Update from 0.5.2 or earlier
++++++++++++++++++++++++++++

If you update from 0.5.2 or earlier, you need a few more
|bin-restauth-manage-link| commands:

.. parsed-literal::

   |bin-restauth-manage| syncdb

   |bin-restauth-manage| migrate Services 0001 --fake
   |bin-restauth-manage| migrate Users 0001 --fake
   |bin-restauth-manage| migrate Groups 0001 --fake

   |bin-restauth-manage| migrate

Update from earlier versions
++++++++++++++++++++++++++++

There are no schema changes in earlier releases.

.. _update-settings:

Use new settings
================

.. _update_settings_0.6.4:

New/updated settings in 0.6.4
+++++++++++++++++++++++++++++

* :setting:`SECURE_CACHE` is now ``True`` by default. If you want to restore the
  previous default behaviour, set it to ``False``.
* RestAuth 0.6.4 brings a slightly new module layout. Modules no longer use the
  ``RestAuth`` prefix, except for the settings-module itself. So settings that
  define module paths should be stripped of ``RestAuth.``, example::

      #before:
      #VALIDATORS = (
      #   'RestAuth.Users.validators.DrupalValidator',
      #   ....
      #)
      #
      #after:
      #VALIDATORS = (
      #   'Users.validators.DrupalValidator',
      #   ....
      #)

  The following settings are likely to be affected by this change:
  ``VALIDATORS``, ``PASSWORD_HASHERS``, ``SERVICE_PASSWORD_HASHER``,
  ``USER_BACKEND``, ``GROUP_BACKEND``, ``PROPERTY_BACKEND``.

.. _update_settings_0.6.1:

New/updated settings in 0.6.1
+++++++++++++++++++++++++++++

* The ``HASH_ALGORITHM`` and ``HASH_FUNCTIONS`` settings introduced in
  :ref:`0.5.3 <update_settings_0.5.3>` have been deprecated in favour of the
  :setting:`PASSWORD_HASHERS` setting provided by Django itself. Hashers are now
  classes, which means that any custom hashers have to be rewritten. Please see
  :doc:`/config/custom-hashes` for more information.

  The default is the same as the `Django default
  <https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers>`_ but
  with additional hashers for MediaWiki, Apr1 (Apache .htaccess files) and for
  standard SHA-512-hashes with salts. As a consequence, RestAuth now by default
  stores User hashes with `PBKDF2 <http://en.wikipedia.org/wiki/PBKDF2>`_.
* Django now supports storing its user-data, properties and groups in different
  backends. The default is fine for existing installations, but you can now
  store data in different backends if you like. Please see
  :doc:`/config/backends` for more information.
* The ENABLE_SESSIONS parameter was removed. The functionality was never
  properly tested anyway.
* The :setting:`SERVICE_PASSWORD_HASHER` setting may be used to speed up
  RestAuth.
* The :setting:`SECURE_CACHE` setting defines if RestAuth should store sensitive
  data in its caching framework. The default is False and this setting should
  only be set to True if you consider the cache store secure.
* The :setting:`CONTENT_HANDLERS` setting now defines content handlers usable
  for RestAuth. RestAuth keeps a global list of content handlers and no longer
  creates new handler instances upon every page load.

.. _update_settings_0.6.0:

New settings in 0.6.0
+++++++++++++++++++++

In 0.5.3 and earlier, nested group membership was determined by a rather complex
algorithm with many database queries. The check is now done entirely within the
database and is much faster. As a side-effect, the recursion depth is now
configurable, with the new :setting:`GROUP_RECURSION_DEPTH` setting.

The new default is 3, while the old code used the hard-coded recursion depth of
10. Feel free to increase this value, but note that greater recursion depth
decreases performance. If you do not use nested groups at all, you can set
:setting:`GROUP_RECURSION_DEPTH` to 0 to completely disable nested groups.

.. _update_settings_0.5.3:

New settings in 0.5.3
+++++++++++++++++++++

HASH_FUNCTIONS and HASH_ALGORITHM
_________________________________

In version 0.5.2 and earlier, RestAuth only supports hash algorithms supported
by the `hashlib module <http://docs.python.org/library/hashlib.html>`_ and the
special value ``mediawiki`` to use MediaWiki style MD5 hashes.

In version 0.5.3 and later, it is possible to :ref:`implement your own hash
functions <own-hash-functions>` and add them using the :setting:`HASH_FUNCTIONS`
setting. The ``mediawiki`` hash function is also implemented in this way.

The default already enables the mediawiki hash function (as well as the new
support for .htaccess files), so there is no need for any configuration change.


VALIDATORS vs. SKIP_VALIDATORS
______________________________

In version 0.5.2 and earlier, only a pre-defined set of validators was supported
and most validators were enabled by default. It was only possible to skip some
of the pre-defined validators with the ``SKIP_VALIDATORS`` setting.

In version 0.5.3 and later, no validators are enabled by default and you have to
explicitly enable validators using the :setting:`VALIDATORS` setting, please see
the documentation for an example on how to enable validators. Our page on
:doc:`/config/username-validation` has a list of validators
shipping with RestAuth as well as documentation on how to implement your own
validators.

To just restore the previous behaviour, add this to |file-settings-link|:

.. code-block:: python

   VALIDATORS = [
       'RestAuth.Users.validators.mediawiki',
   ]

... and remove the ``SKIP_VALIDATORS`` setting.
