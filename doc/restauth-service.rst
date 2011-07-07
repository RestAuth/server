restauth-service
================

.. only:: man

   Synopsis
   --------

   **restauth-service** [**-h**] *command* [*option*] ... [*args*] ...

   Description
   -----------

*restauth-service* may be used to manage services that connect to RestAuth. A
service is a system that wants to use RestAuth to store users, preferences and
groups.

RestAuth stores a name (which may not include a ':') and a password that
identify the service. A service additionally has zero or more IPv4 or IPv6
addresses associated with it, a service can only authenticate from the given
adresses. 

Usage
-----

.. only:: html
   
   .. literalinclude:: gen/restauth-service-usage.rst

Use one of the commands (either add, view, ls, set-hosts, set-password or rm) to
perform the respective operation. Each command usually requires more arguments
to it, see the respective section for arguments (and possible options) for each
command.

.. only:: html

   Getting runtime help
   ^^^^^^^^^^^^^^^^^^^^^^^

   To get an authoritative list of available commands, use::
      
      restauth-service --help

   If you want more information on a specific comannd, do::
   
      restauth-service command --help
   
   ... or see the :ref:`service-available-commands` section below.

.. only:: man

    Use "**restauth-service --help**" to get an authoritative list of available
    commands. If you want help on a specific command, use "**restauth-service** 
    *command* **--help**" or see the 
    :ref:`AVAILABLE COMMANDS<service-available-commands>` section below.

Examples
--------

.. example:: **restauth-service add** *example.com*

   Add the service *example.com* and prompt for a password.

   
.. example:: **restauth-service add -**\ **-gen-password** *example.com* *127.0.0.1* *::1*

   Add the service *example.com* and associate *127.0.0.1* and *::1* with it.
   Also generate a password and print it to stdout, so it can be used for
   configuration of the actual service

.. example:: **restauth-service ls**

   List all available services.

.. example:: **restauth-service view** *example.com*

   View all details of the service *example.com*.

.. example:: **restauth-service set-password -**\ **-password=**\ *foobar* *example.com*

   Set the password of the service *example.com* (which must already exist)
   to *foobar*. 

.. example:: **restauth-service set-hosts** *example.com* *192.168.0.1* *192.168.0.2*

   Enable the service *example.com* for the hosts *192.168.0.1* *192.168.0.2*.
   Note that this removes any previously configured hosts.

.. example:: **restauth-service remove** *example.com*

   Remove the service *example.com* from RestAuth. This will also remove any
   groups defined for the service, see **restauth-groups**\ (1).

.. _service-available-commands:

Available commands
------------------

The following subsections never document the '-h' parameter for clarity.

.. include:: gen/restauth-service-commands.rst

Influential environment variables
---------------------------------

.. include:: includes/env-variables.rst

.. only:: man

   See Also
   ^^^^^^^^

   **restauth-users**\ (1), **restauth-groups**\ (1)
