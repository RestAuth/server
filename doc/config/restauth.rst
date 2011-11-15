Configuring RestAuth
====================

RestAuth is configured like any other Django project, in the file :file:`settings.py`. You
should never edit this file directly, instead always edit the (much better documented)
:file:`localsettings.py`. This file is included by :file:`settings.py` and should, as its name
suggests, set anything that is specific to your local installation. The file includes any settings
you are likely to edit, but you can actually configure any `Django setting
<https://docs.djangoproject.com/en/dev/ref/settings/>`_ you want there. Please consult
:doc:`the Settings reference</config/all-config-values>` on noteworthy configuration variables.


By default, you have to do very few modifications to :file:`localsettings.py`. The only settings you
*have to* configure is :setting:`DATABASES` and :setting:`SECRET_KEY`. We do provide some limited
help on :doc:`how to create a database <database>`.

Get RestAuth up & running
-------------------------

After you have successfully installed RestAuth, there are only two things you have to do to get a
working RestAuth server:

* :doc:`configuring your webserver </config/webserver>`
* :doc:`create a database </config/database>`

After you have done that, you still need to tell RestAuth about the services that may use it. You
can do this with the command-line script :doc:`restauth-service </restauth-service>`. After that,
all that is left is to configure the services themself.

Advanced configuration
----------------------

.. toctree::
   :maxdepth: 1
   
   all-config-values
   username-validation
   multiple-instances
   database-replication