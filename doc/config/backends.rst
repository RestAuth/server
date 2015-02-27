Backends
========

RestAuth uses backends to manage data. This means that you can configure
different storage backends and even write your own backends if you have already
have a custom service storing data.

Configuring backends
____________________

To configure what backend to use, use the :setting:`DATA_BACKEND`. Backends
shipping with RestAuth are listed below, if you want to develop your own
backend, please see :doc:`/developer/backends`.

Note that each backend may use settings not listed in the
:doc:`settings reference </config/all-config-values>`. For backend-specific
settings, please consult the backends documentation.

.. autoclass:: backends.django.DjangoBackend
