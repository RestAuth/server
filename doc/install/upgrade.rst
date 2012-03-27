Upgrade notes
-------------

.. _upgrade_0.5.2:

from version 0.5.2
==================
In version 0.5.3, a new UNIQUE constraint was added for groups: A group cannot have the same name
AND service as any other group. This was previously ensured only in software. Use
``restauth-manage sql`` to get an SQL-shell of your RestAuth installation.

Additionally, some additional indexes where added.

MySQL
+++++
Use the following SQL commands:

.. code-block:: sql

   ALTER TABLE Groups_group ADD UNIQUE (name, service_id);
   
After that, run the ``syncdb`` command of :doc:`/bin/restauth-manage` to create the new indices.

PostgreSQL
++++++++++

.. code-block:: sql
   
   ALTER TABLE Groups_group ADD CONSTRAINT service_id_name_key UNIQUE (name, service_id);

After that, run the ``syncdb`` command of :doc:`/bin/restauth-manage` to create the new indices.

SQLite
++++++

SQLite does not support adding UNIQUE constraints to existing tables. Please use :doc:`/bin/restauth-manage`
to dump existing data, recreate the database, and reload that data.

.. code-block:: bash

   user@host:~ $ restauth-manage dumpdata > dump.json
   user@host:~ $ rm <path-to-sqlite-db>
   user@host:~ $ restauth-manage syncdb --noinput
   user@host:~ $ restauth-manage loaddata dump
   user@host:~ $ rm dump.json
   
.. NOTE:: Running RestAuth using SQLite is still not recommended.

.. _upgrade_0.5.2_settings:

Settings
++++++++

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

To just restore the previous behaviour, add this to :file:`localsettings.py` (or
:file:`/etc/restauth/settings.py` if you installed using our Debian/Ubuntu packages):

.. code-block:: python

   VALIDATORS = [
       'RestAuth.Users.validators.mediawiki',
   ]
   
... and remove the ``SKIP_VALIDATORS`` setting.