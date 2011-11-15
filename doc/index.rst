.. RestAuth documentation master file, created by
   sphinx-quickstart on Sun Jul  3 12:18:18 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to RestAuth!
====================

Welcome to **RestAuth**, a lightweight webservice that provides shared authentication, authorization
and preferences. RestAuth does not attempt to provide "one account for the web" like `OpenId
<http://en.wikipedia.org/wiki/OpenID>`_ or `OAuth <http://en.wikipedia.org/wiki/OAuth>`_ but instead
allows multiple systems to directly use the same userbase, much like the way LDAP or Kerberos
is commonly used. Since RestAuth is Free Software, please feel free to :doc:`contribute </contribute>`.

RestAuth focuses on being very easy to setup and maintain. Installation is possible within just a
few minutes, if you have some system administration experience. RestAuth is also very flexible,
allowing you to import and use accounts from many other systems. You can also block registrations of
accounts where the username is not compatible with some systems you use. 

RestAuth is the server-side reference implementation of the `RestAuth protocol
<https://restauth.net/Specification>`_. RestAuth is written in `Python
<http://www.python.org>`_ and is uses the `Django webframework <http://djangoproject.com/>`_. As
such, it can run on a variety of operating systems, using any webserver and database system
supported by Django (see the `Django installation instructions
<https://docs.djangoproject.com/en/dev/topics/install/>`_ for a list of supported systems). 

RestAuth is Free Software, licensed unter the `GNU General Public Licence, version 3
<http://www.gnu.org/licenses/gpl.html>`_. 


.. Contents:
   .. toctree::
      :maxdepth: 1

Installation
============

.. toctree::
   :maxdepth: 1

   install/from-source
   install/debian-ubuntu

Getting started
===============

.. toctree::
   :maxdepth: 1

   config/restauth
   config/webserver
   config/database

Advanced configuration
======================

.. toctree::
   :maxdepth: 1
   
   config/all-config-values
   config/username-validation
   config/multiple-instances
   config/database-replication

Commandline scripts
===================

RestAuth provides command-line scripts to locally interact with RestAuth. They are required for
some functionality (managing services and global groups) that is not available via the RestAuth
protocol.

.. toctree::
   :maxdepth: 1
   
   restauth-service
   restauth-user
   restauth-group
   restauth-import
   
Migrating to RestAuth
=====================

If you already have some systems running that should use RestAuth, you have to import their
user databases. This section documents scripts and notes vor various systems.

.. toctree::
   :maxdepth: 1
   
   migrate/general
   migrate/import-format
   migrate/mediawiki
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

