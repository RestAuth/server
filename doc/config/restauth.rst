Overview
========

After you have successfully :ref:`installed RestAuth <index_installation>`, there are only two
things you have to do to get a working RestAuth server:

.. toctree::
   :maxdepth: 1
   
   configuring your webserver </config/webserver>
   create and configure a database </config/database>

After you have done that, you still need to tell RestAuth about the services that may use it. You
can do this with the command-line script :doc:`restauth-service </restauth-service>`. After that,
all that is left is to configure the services themself.

RestAuth configuration and management
-------------------------------------

RestAuth is configured in the file :file:`localsettings.py`. The file shipping with RestAuth already
includes all variables and documentation for what you will likely want to change. Please also
consult :doc:`the settings reference</config/all-config-values>` on noteworthy configuration
variables. By default, you have to do very few modifications to :file:`localsettings.py`, the only
thing you really have to do is :doc:`configure a database </config/database>`.

.. NOTE:: For Django experts

   RestAuth, as a Django project, is of course really configured like any other project, with the
   file :file:`settings.py`. This file defines defaults, includes :file:`localsettings.py` and sets
   some settings intelligentely based on what you set in :file:`localsettings.py`. You can of course
   set any `Django setting <https://docs.djangoproject.com/en/dev/ref/settings/>`_ you want in
   :file:`localsettings.py`. 

You can manage your RestAuth server completely from the command-line. Please see the overview of
available command-line scripts:

.. toctree::
   :maxdepth: 1
   
   /config/manage

Advanced configuration
----------------------

.. toctree::
   :maxdepth: 1
   
   all-config-values
   username-validation
   multiple-instances
   database-replication