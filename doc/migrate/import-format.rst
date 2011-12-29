RestAuth import data format
===========================

The *RestAuth import data format* describes a file format to import data into RestAuth. Such files
are typically created by systems from where existing account data should be exported and is imported
by |restauth-import|.

.. NOTE::
   You only need this documentation if you want to write a new exporter (i.e. for a system for which
   no such exporter is yet available). If you write a new exporter, please feel free to
   :doc:`contribute </developer/contribute>` it.

General
-------

The fileformat uses `JSON <http://www.json.org/>`_ to encode the data. JSON is the primary data
interchange format used by RestAuth, both encoders and decoders are widely available in almost any
programming language.

On the topmost level, an import file must contain a dictionary containing up to three key/value
pairs, identified by these keys:

* **services** for importing :ref:`import-format-services`.
* **users** for importing :ref:`import-format-users`.
* **groups** for importing :ref:`import-format-groups`.

All keys are optional, but the file must of course contain at least one key to be useful. Also see
the :ref:`import-format-example` section for a detailed example.

The :doc:`import script </restauth-import>` will import services, users and groups in precisely this
order. This is important because groups may reference services and users that are imported in the
same file and thus wouldn't yet exist if the order were any different.

.. _import-format-services:

Services
--------

The value for the **services** key must be itself a dictionary where each key represents the name
of the service and the corresponding value is again a dictionary describing the service. The file
format supports two key/value pairs here:

* **password** is either a string representing the cleartext password or a dictionary with three
  key/value pairs: **algorithm**, **salt** and **hash**. In the latter case, this must of course be
  something that is supported by your Django installation.
  
  If the service already exists, passwords won't be overwritten unless you give the
  **-**\ **-overwrite-passwords** parameter.
  
* **hosts** is a list of strings containing one or more hostnames that this service would connect
  from.
  
  If the service already exists, hosts will be added to this service.
  
Both elements are optional and can also be configured by the :doc:`/restauth-service` script.

Example::
   
    {
        'services': {
            "example.at": {},
            "example.org": {
                "hosts": [
                    "127.0.0.1",
                    "::1"
                ]
            },
            "example.net": {
                "password": {
                    "salt": "saltfrominput",
                    "hash": "hashfrominput",
                    "algorithm": "md5"
                }
            },
            "example.com": {
                "password": "anotherrawpassword",
                "hosts": [
                    "127.0.0.1",
                    "::1"
                ]
            }
        }
    }
    
In this example, only *example.com* is actually usable (from localhost). The other services may
still be usable if the service already exists. In the case of *example.org*, for example, the
two named hostnames would be added to an existing service with the same name.

.. _import-format-users:

Users
-----

The value for the **users** must itself be a dictionary where each key represents the name of the
user and the corresponding value is again a dictionary describing the user. The file format supports
two key/value pairs here:

* **password** works the same way as with :ref:`import-format-services`. Note that an empty string
  is equal to setting an unusable password.
* **properties** is a dictionary containing any user properties. Values are usually strings except
  for the special values **date_joined** and **last_login**, which are a float representing a
  standard unix timestamp. If the two latter properties are not given, the user joined and logged in
  "now".
  
  If a named property already exists, its not overwritten unless you give the
  **-**\ **-overwrite-properties** command line parameter. The last_login and date_joined properties
  are handled differently: restauth-import will use the earlier joined date and the later logged-in
  date.
  
Example::

    {
        "users": {
            "bareuser": {},
            "onlypassword": {
                "password": "this user only has a password, no properties."
            },
            "mati": {
                "password": "rawpassword",
                "properties": {
                    "email": "mati@example.com",
                    "last_login": 1300731615.060394,
                    "full name": "Mathias Ertl",
                    "date_joined": 1300730615.060394
                }
            },
            "full example": {
                "password": {
                    "salt": "randomstring",
                    "hash": "secrethash",
                    "algorithm": "md5"
                },
                "properties": {
                    "email": "mati@fsinf.at",
                    "last_login": 1310731615.060394,
                    "full name": "foo foo",
                    "date_joined": 1310730615.060394
                }
            }
        }
    }

.. _import-format-groups:

Groups
------

The value for the **groups** must itself be a dictionary where each key represents the name of the
group and the corresponding value is again a dictionary describing the group. The file format
supports three key/value pairs here:

* **service** is a string naming the service this group belongs to. A null value or ommitting this
  value is equivalent to a group thats not associated with any service.
* **users** is a list of strings naming the users that are a member of a group. If the group already
  exists, the users are *added* to this group.
* **subgroups** is a list of dictionaries describing subgroups. Such a dictionary contains a
  service and a name identifying the subgroup.
  
Note that subgroup relationships are only added after all groups are added, so the order is not
in any way important.

Example::

    {
        "groups": {
            "admins": {
                "users": [
                    "mati"
                ],
                "service": "example.com",
                "subgroups": [
                    {   
                        "name": "users",
                        "service": "example.com"
                    }
                ]
            },
            "users": {
                "users": [
                    "foobar"
                ],
                "service": "example.com"
            }
        }
    }


.. _import-format-example:

Example
-------

This is a full example of a file that can be used by :doc:`/restauth-import`::

    {
        "services": {
            "example.org": {
                "password": "passwordfrominputdata"
            },
            "example.net": {
                "password": {
                    "salt": "saltfrominput",
                    "hash": "hashfrominput",
                    "algorithm": "md5"
                }
            },
            "example.com": {
                "hosts": [
                    "127.0.0.1",
                    "::1"
                ]
            }
        },
        "users": {
            "bareuser": {},
            "foobar": {
                "password": "rawpassword",
                "properties": {
                    "email": "mati@fsinf.at",
                    "last_login": 1300731615.060394,
                    "full name": "Another name",
                    "date_joined": 1300730615.060394
                }
            },
            "mati": {
                "password": {
                    "salt": "randomstring",
                    "hash": "secrethash",
                    "algorithm": "md5"
                },
                "properties": {
                    "email": "mati@fsinf.at",
                    "last_login": 1310731615.060394,
                    "full name": "Mathias Ertl",
                    "date_joined": 1310730615.060394
                }
            }
        },
        "groups": {
            "admins": {
                "users": [
                    "mati"
                ],
                "service": "example.com",
                "subgroups": [
                    {
                        "name": "users",
                        "service": "example.com"
                    }
                ]
            },
            "users": {
                "users": [
                    "foobar"
                ],
                "service": "example.com"
            }
        }
    }
    
Note again that you can easily not import any one of the above things simply by ommitting the
appropriate keys.