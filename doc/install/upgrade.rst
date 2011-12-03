Upgrade notes
-------------

from version 0.5.2
==================
In version 0.5.3, a new UNIQUE constraint was added for groups: A group cannot have the same name
AND service as any other group. This was previously ensured only in software. Use
``restauth-manage sql`` to get an SQL-shell of your RestAuth installation.

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

MySQL
+++++
Use the following SQL command:

.. code-block:: sql

   ALTER TABLE Groups_group ADD UNIQUE (name, service_id);

PostgreSQL
++++++++++

.. code-block:: sql
   
   ALTER TABLE Groups_group ADD CONSTRAINT service_id_name_key UNIQUE (name, service_id);