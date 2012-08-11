Installation on Red Hat Enterprise Linux (RHEL)
-----------------------------------------------

RestAuth is not included in Red Hat Enterprise Linux. The current version does
not ship with a Python interpreter that works with it, so it is hardly possible
to install RestAuth on the current version of that distribution.

.. NOTE:: Since RestAuth is already included in Fedora, it will be included in
   the next release of Red Hat Enterprise Linux.

Installation on Fedora
----------------------

RestAuth is included in Fedora 16 or later. To install RestAuth, just do:

.. code-block:: bash

   yum install restauth

Once you have installed RestAuth, you can go on :doc:`configuring your webserver
</config/webserver>` and :doc:`configuring RestAuth </config/restauth>`.

.. _fedora-update:

Updating the source
===================

You can update the source code with the regular process:

.. code-block:: bash

   yum update restauth

After you updated the source, don't forget to :ref:`update your database schema
<update-database>` and :ref:`check for new settings <update-settings>`.
