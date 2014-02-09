Installation with pip
=====================

RestAuth is also :pypi:`also included in PyPI <RestAuth>`.  That makes it very easy to install this
library using :command:`pip` and virtualenv:

.. code-block:: bash

   virtualenv RestAuth
   cd RestAuth
   source bin/activate
   pip install RestAuth

All non-source files are installed into `RestAuth/`. The configure RestAuth, copy the example
configuration file in :file:`RestAuth/config/localsettings.py.example` to
:file:`RestAuth/config/localsettings.py`:

.. code-block:: bash

   cp RestAuth/config/localsettings.py.example RestAuth/config/localsettings.py

.. include:: /includes/next-steps.rst

.. _pip-update:

Update
------

To update to a new release, just use ``pip install -U`` inside your virtualenv:

.. WARNING:: All changes to source files (e.g. the wsgi script) will be overwritten. If you need to
   make changes, copy the file to a different location first.

.. code-block:: bash

   source bin/activate
   pip install -U RestAuth

... and be sure to follow the :doc:`update instructions </install/update>`.
