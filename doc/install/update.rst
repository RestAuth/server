Update instructions
-------------------

Updating RestAuth consists of three steps: First you have to update the source code and database
schema. You should also check for new available settings when a new version becomes available.

Update source
=============

The specific installation instructions for your platform provide documentation on how to update
your source code:

* :ref:`from source <source-update>`
* :ref:`Debian/Ubuntu <debian-update>`
* :ref:`Fedora <fedora-update>`
* :ref:`Arch Linux <arch-update>`

.. _update-database:

Update database schema
======================

Starting from version 0.5.3, we use `Django South
<http://south.readthedocs.org/en/latest/index.html>`_ to handle schema migrations. If you installed
from source, simply use |bin-restauth-manage-link| to update your schema:

.. parsed-literal:: |bin-restauth-manage| migrate

Update from 0.5.2 or earlier
++++++++++++++++++++++++++++

If you update from 0.5.2 or earlier, you need a few more |bin-restauth-manage-link| commands:

.. parsed-literal::

   |bin-restauth-manage| syncdb
   
   |bin-restauth-manage| Services 0001 --fake
   |bin-restauth-manage| Users 0001 --fake
   |bin-restauth-manage| Groups 0001 --fake
   
   |bin-restauth-manage|

.. WARNING:: The process of introducing Django-South is a bit fragile. ALWAYS backup your database
   before doing this. If all fails, please :doc:`contact us </developer/contribute>`.

Update from earlier versions
++++++++++++++++++++++++++++

There are no schema changes in earlier releases.

.. _update-settings:

Use new settings
================

.. _update_settings_0.5.3:

New Settings in  0.5.3
++++++++++++++++++++++

HASH_FUNCTIONS and HASH_ALGORITHM
_________________________________

In version 0.5.2 and earlier, RestAuth only supports hash algorithms supported by the `hashlib
module <http://docs.python.org/library/hashlib.html>`_ and the special value ``mediawiki`` to use
MediaWiki style MD5 hashes.

In version 0.5.3 and later, it is possible to :ref:`implement your own hash functions
<own-hash-functions>` and add them using the :setting:`HASH_FUNCTIONS` setting. The ``mediawiki``
hash function is also implemented in this way.

The default already enables the mediawiki hash function (as well as the new support for .htaccess
files), so there is no need for any configuration change.


VALIDATORS vs. SKIP_VALIDATORS
______________________________

In version 0.5.2 and earlier, only a pre-defined set of validators was supported and most validators
were enabled by default. It was only possible to skip some of the pre-defined validators with the
``SKIP_VALIDATORS`` setting.

In version 0.5.3 and later, no validators are enabled by default and you have to explicitly enable
validators using the :setting:`VALIDATORS` setting, please see the documentation for an example on
how to enable validators. Our page on :doc:`/config/username-validation` has a list of validators
shipping with RestAuth as well as documentation on how to implement your own validators.

To just restore the previous behaviour, add this to |file-settings-link|:

.. code-block:: python

   VALIDATORS = [
       'RestAuth.Users.validators.mediawiki',
   ]
   
... and remove the ``SKIP_VALIDATORS`` setting.
