Backends
========

RestAuth uses backends to store data. RestAuth knows three different types of
backends:

:ref:`user-backends`
   Store user data.
:ref:`property-backends`
   Store user properties.
:ref:`group-backends`
   Store groups.

RestAuth can use different backends for each individual task, but property- and
group-backends may depend on a specific user-backend being used. Most
prominently, the default backends
:py:class:`~backends.django.DjangoPropertyBackend` and
:py:class:`~backends.django.DjangoGroupBackend` require that you
also use :py:class:`~backends.django.DjangoUserBackend`.

Configuring backends
____________________

To configure what backend to use, use the :setting:`USER_BACKEND`,
:setting:`PROPERTY_BACKEND` and :setting:`GROUP_BACKEND` settings. Backends
shipping with RestAuth are listed below, if you want to develop your own
backend(s), please see :doc:`/developer/backends`.

Note that each backend may use settings not listed in the
:doc:`settings reference </config/all-config-values>`. For backend-specific
settings, please consult the backends documentation.

.. _user-backends:

User backends
_____________

A user backend handles the most basic operations related to users. The user
backend is used to create and delete users as well as to check and update a
users password.

.. autoclass:: backends.django.DjangoUserBackend
.. autoclass:: backends.memory_backend.MemoryUserBackend

.. _property-backends:

Property backends
_________________

A property backend handles user properties such as email, full
name and so on.

.. autoclass:: backends.django.DjangoPropertyBackend

.. autoclass:: backends.redis_backend.RedisPropertyBackend
.. autoclass:: backends.memory_backend.MemoryPropertyBackend

.. _group-backends:

Group backends
______________

A group backend handles user groups. Groups may be used by a service for
authorization or similar purposes.

.. autoclass:: backends.django.DjangoGroupBackend
.. autoclass:: backends.memory_backend.MemoryGroupBackend
