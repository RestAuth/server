Installation from source
========================

Requirements
------------

RestAuth is written as a *bleeding edge* project and thus requires relatively new software versions.

* `Python 2.6 <http://www.python.org/>`_ or later
* `Django 1.3 <https://www.djangoproject.com/>`_ - RestAuth is written as a Django project
* `RestAuthCommon <https://redmine.fsinf.at/projects/restauthcommon>`_
* The `mimeparse <https://code.google.com/p/mimeparse/>`_ module is required by RestAuthCommon
* The `argparse <http://docs.python.org/library/argparse.html>`_ module ships with Python 2.7 and is
  available for Python 2.6

.. Note:: Although Django itself still supports Python 2.5, RestAuth is only compatible with
   Python 2.6 or later. 

Get source
----------

From git
++++++++

This project is developed on `git.fsinf.at <https://git.fsinf.at/>`_. You can view the source code
at `git.fsinf.at/restauth/server  <https://git.fsinf.at/restauth/server>`_. To clone the
repository to a directory named "RestAuth", simply do:

.. code-block:: bash

   git clone http://git.fsinf.at/restauth/server.git RestAuth

Older versions are marked as tags. You can view available tags with :command:`git tag -l`. You can
use any of those versions with :command:`git checkout`, for example :command:`git checkout 1.0`.
To move back to the newest version, use :command:`git checkout master`.

If you ever want to update the source code, just use:

.. code-block:: bash

   python setup.py clean
   git pull
   
... and do the same as if you where
:ref:`doing a new installation <install_from-source_installation>`.

Official releases
+++++++++++++++++

There are no "official releases* yet, hence no tarballs to download ;-).

.. _install_from-source_installation:

Installation
------------

Installation itself is very easy. Just go to the directory where your source is located ("RestAuth"
in the above example) and just run:

.. code-block:: bash

   python setup.py build
   python setup.py install
   
Once you have installed RestAuth, you can go on :doc:`configuring your webserver
<../config/webserver>` and :doc:`configuring RestAuth <../config/restauth>`.

Run tests
---------

RestAuth features an extensive test suite. You can run those tests using:

.. code-block:: bash

   python setup.py test
   
Note that you can run these tests even if you already installed RestAuth or locally configured your
RestAuth installation. The tests will *always* use their own temporary database.

Build documentation
-------------------

To generate the most recent documentation (the newest version of the document you're currently
reading), just run:

.. code-block:: bash

   python setup.py build_doc