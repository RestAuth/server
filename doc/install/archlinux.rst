Installation on Archlinux
=========================

Restauth-common and the RestAuth reference implementation are currently available in the AUR (Arch
User Repositories).

Installing from the AUR website
-------------------------------
The RestAuth-Server has the following AUR dependencies

* `python-mimeparse <https://aur.archlinux.org/packages.php?ID=43681>`_
* `restauth-common-git <https://aur.archlinux.org/packages.php?ID=58846>`_
* `restauth-server-git <https://aur.archlinux.org/packages.php?ID=58847>`_

To install each of these, follow this guide:
`AUR | ArchWiki <https://wiki.archlinux.org/index.php/AUR#Installing_packages>`_

Install using yaourt
--------------------
If you have `yaourt <https://wiki.archlinux.org/index.php/Yaourt>`_ installed on your system, just
run the following:

.. code-block:: bash
   
   yaourt -S restauth-server-git

.. _arch-update:

Updating the source
-------------------

You can update the source code with the regular process:

.. code-block:: bash

   yaourt -Syua

After you updated the source, don't forget to :ref:`update your database schema <update-database>`
and :ref:`check for new settings <update-settings>`.
