Installation on Debian/Ubuntu
=============================

The RestAuth project provides APT repositories for all software it maintains.  Repositories are
available for all distributions that are currently maintained by the Debian project and Canonical
respectively.

.. NOTE:: Repositories for older distributions may contain older versions of RestAuth. If you use
   an older distribution, install the ``restauth-doc`` package to get documentation for the
   specific version of RestAuth.

Adding our APT repository
-------------------------

To add the repositories, simply add this line to your :file:`/etc/apt/sources.list` file::

   deb http://apt.fsinf.at <dist> restauth

... where :samp:`{<dist>}` is any of the supported distributions. At the time of writing, possible
values are ``lucid``, ``oneiric``, ``precise``, ``squeeze`` or
``wheezy``.  Please see the WikiPedia pages for `Ubuntu
<http://en.wikipedia.org/wiki/List_of_Ubuntu_releases#Table_of_versions>`_ and `Debian
<http://en.wikipedia.org/wiki/Debian#Release_history>`_ to see how they map to your installation.
You can also check the `APT repository itself <http://apt.fsinf.at/dists>`_ for a list of available
distributions (don't forget to check the 'Last modified' timestamp!).

Once you added the repository, you have to install the fsinf GPG keyring used for signing the
repositories, so you won't get any warnings when updating. You can either install the
``fsinf-keyring`` package using:

.. code-block:: bash

   apt-get update
   apt-get install fsinf-keyring
   apt-get update

or download and add the key directly using:

.. code-block:: bash

   wget -O - http://packages.spectrum.im/keys/apt-repository@fsinf.at | apt-key add -
   apt-get update

Install RestAuth
----------------

Once you have added the repositories, installing RestAuth is as simple as

.. code-block:: bash

   apt-get install restauth

Your settings-file is located at |file-settings-debian-as-file|, the WSGI file is located at
|file-wsgi-debian-as-file| and all command-line scripts will be in :file:`/usr/bin` (so you can
just execute e.g. |bin-restauth-manage-debian-as-cmd|).

.. include:: /includes/next-steps.rst

.. _debian-update:

Updating the source
-------------------

You can update the source code with the regular process:

.. code-block:: bash

   apt-get update
   apt-get install restauth

After you updated the source, don't forget to :ref:`update your database schema <update-database>`
and :ref:`check for new settings <update-settings>`.
