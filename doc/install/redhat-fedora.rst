Installation on Red Hat Enterprise Linux
----------------------------------------

RestAuth is not included in Red Hat Enterprise Linux. The current version does not ship with a
Python interpreter that works with it, so it is hardly possible to install RestAuth on the current
version of that distribution.

.. NOTE:: Since RestAuth is already included in Fedora, it will be included in the next release of
   Red Hat Enterprise Linux.

Installation on Fedora
----------------------

RestAuth is included in Fedora 16 or later. To install RestAuth, just do:

.. code-block:: bash

   yum install restauth
   
Once you have installed RestAuth, you can go on :doc:`configuring your webserver
</config/webserver>` and :doc:`configuring RestAuth </config/restauth>`.