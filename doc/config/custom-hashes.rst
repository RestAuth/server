Custom password hashes
----------------------

RestAuth can understand custom hashing algorithms if you add functions to handle them with the
:setting:`HASH_FUNCTIONS` setting. This is useful if you want to import userdata from a different
system that stores passwords using an unusual hashing algorithm.

You can :ref:`implement your own hashing algorithm <own-hash-functions>` if you intend to import
data from a system not supported by RestAuth. If you set :setting:`HASH_ALGORITHM` to one of the
algorithms you add to this setting, RestAuth will also store hashes using this algorithm. This is
useful if you plan to later export data to such a system.

.. _available-hash-functions:

Available hash functions
========================

.. automodule:: RestAuth.Users.hashes
   :members: apr1, crypt, mediawiki
   
.. _own-hash-functions:

Implement your own hash functions
=================================

Implementing your own hash function is very easy. The only thing you need to do is implement a
function with the following signature:

.. code-block:: python

   def my_algorithm(secret, salt):
       # do some magic
       return hash
       
There are a few things to note here:

* ``my_algorithm`` is the function name and encodes a custom name of your algorithm. The only
  restrictons for a name are that it is a valid function name (i.e. no dashes (``-``)) and that it
  is not one of the algorithms implemented by the `hashlib module
  <http://docs.python.org/library/hashlib.html>`_ shipping with python. The name is the same as the
  name of the :ref:`algorithm in the password dictionary <import-format-services>` of the import
  data format.
* The ``secret`` argument is the plain password.
* The ``salt`` argument may optionally be ``None`` if the algorithm in question may not use a salt.
* The function must return the valid hash of ``secret`` using the ``salt`` supplied (if any).

Once you implemented your hash function, all you have to do is append the path of that function to
:setting:`HASH_FUNCTIONS` in :file:`localsettings.py`:

.. code-block:: python

   HASH_FUNCTIONS = [
       'RestAuth.Users.hashes.mediawiki',
       'RestAuth.Users.hashes.crypt',
       'RestAuth.Users.hashes.apr1',
       'path.to.your.func.algorithm',
   ]


Example
+++++++

A common scenario is that a system you want to import data from does not use a very unusual hashing
algorithm, but rather the salt is used in a different way. RestAuth prepends the salt to the
password without any delimiter. By contrast, i.e. MediaWiki delimits the salt and password with a
dash (``-``). Another scenario is that the hash is applied multiple times to improve security. Here
are two examples:

.. code-block:: python
   
   import hashlib
   
   def custom_delimiter(secret, salt):
       """
       This hash is the md5-hash of the salt, a dash (``-``) and the md5-hash of the password.
       """
       secret_hash = hashlib.md5(secret).hexdigest()
       return hashlib.md5('%s-%s' % (salt, secret_hash)).hexdigest()
       
   def multiple_rounds(secret, salt):
       """
       Uses plain sha512 but uses 1000 rounds of hashing.
       """
       i = 0
       hash = hashlib.sha512('%s%s' % (salt, secret)).hexdigest()
       while i < 1000:
           hash = hashlib.sha512('%s%s' % (salt, secret)).hexdigest()
           i += 1
	   
       return hash
       