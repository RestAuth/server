Installation from source
========================

Requirements
------------

RestAuth has the following requirements:

* `Python`_ 2.7 or later or Python 3.2 or later
* `Django`_ 1.7 or later - RestAuth is written as a Django project
* Any database supported by Django that supports transactions, see the `DATABASES`_ setting.
* `RestAuthCommon`_ 0.7.0 or later
* :pypi:`mimeparse` 0.1.4 or later

Additionally, various optional features require additional libraries:

* :pypi:`MySQL-python` if you use MySQL as a :setting:`DATABASES` backend.
* :pypi:`redis` and :pypi:`hiredis` if you want to use the
  :py:class:`~backends.redis_backend.RedisPropertyBackend` or use a Redis instance as a cache
  backend.
* :pypi:`django-hashers-passlib` (>= 0.2) and :pypi:`passlib` (>= 0.6.2) if you want to use most of
  the :doc:`custom password hashers </config/custom-hashes>`.

Get source from git
-------------------

This project is developed `on GitHub <git_>`_. To clone the repository into the :file:`RestAuth`
directory, simply do:

.. code-block:: bash

   git clone https://github.com/RestAuth/server.git RestAuth

Older versions are marked as tags. You can view available tags with :command:`git tag -l`. You can
use any of those versions with :command:`git checkout`, for example :command:`git checkout 0.6.3`.
To move back to the newest version, use :command:`git checkout master`.

.. _source-update:

If you ever want to update the source code, just use:

.. code-block:: bash

   python setup.py clean
   git pull origin master

... and be sure to follow the :doc:`update instructions </install/update>`.

Download official releases
--------------------------

You can download official releases of RestAuth `here <download-releases_>`_. The
latest release is version |restauth-latest-release|.

.. _install_from-source_installation:

Installation
------------

There isn't really anything you have to do besides downloading the source code. To configure
RestAuth, copy :file:`RestAuth/RestAuth/localsettings.py.example` to
:file:`RestAuth/RestAuth/localsettings.py` and edit it to your needs.  The wsgi-script is located
at |file-wsgi-default-as-file|, be sure to include the path of your download directory in the
PYTHONPATH of your WSGI-server.

.. include:: /includes/next-steps.rst

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

.. NOTE:: You can build documentation customized for a specific distribution
   with:

   .. code-block:: bash

      python setup.py build_doc -t debian

   This will customize various paths, binary names etc. for what is used in the
   respective distribution.
