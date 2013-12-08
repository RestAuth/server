# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RestAuth.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import hashlib

from django.contrib.auth.hashers import BasePasswordHasher
from django.contrib.auth.hashers import mask_hash
from django.utils import six
from django.utils.crypto import constant_time_compare
from django.utils.crypto import get_random_string
from django.utils.datastructures import SortedDict


class Sha512Hasher(BasePasswordHasher):
    """A basic sha512 hasher with salt.

    This hasher hashing algorithm that used to be the default before RestAuth
    0.6.1.
    """

    algorithm = 'sha512'

    def _hash2(self, payload):  # pragma: py2
        return hashlib.sha512(payload).hexdigest()

    def _hash3(self, payload):  # pragma: py3
        return hashlib.sha512(bytes(payload, 'utf-8')).hexdigest()

    def encode(self, password, salt):
        hash = self._hash('%s%s' % (salt, password))
        return '%s$%s$%s' % (self.algorithm, salt, hash)

    def verify(self, password, encoded):
        algorithm, salt, hash = encoded.split('$', 3)
        return constant_time_compare(encoded, self.encode(password, salt))

    def safe_summary(self, encoded):  # pragma: no cover
        algorithm, salt, hash = encoded.split('$', 3)
        assert algorithm == self.algorithm
        return SortedDict([
            ('algorithm', algorithm),
            ('salt', mask_hash(salt)),
            ('hash', mask_hash(hash)),
        ])

    if six.PY3:  # pragma: py3
        _hash = _hash3
    else:  # pragma: py2
        _hash = _hash2


class MediaWikiHasher(BasePasswordHasher):
    """
    Returns hashes as stored in a `MediaWiki <https://www.mediawiki.org>`_ user
    database. If salt is a string, the hash returned is the md5 hash of a
    concatenation of the salt, a dash ("-"), and the md5 hash of the password,
    otherwise it is identical to a plain md5 hash of the password.

    Please see the `official documentation
    <http://www.mediawiki.org/wiki/Manual:User_table#user_password>`_ for exact
    details.
    """

    algorithm = 'mediawiki'

    def salt(self):
        return get_random_string(8)

    def encode(self, password, salt=None):
        hash = self._encode(password, salt=salt)
        if salt is None:
            return '%s$$%s' % (self.algorithm, hash)
        else:
            return '%s$%s$%s' % (self.algorithm, salt, hash)

    def _encode2(self, password, salt=None):  # pragma: py2
        if salt is None:
            return hashlib.md5(password).hexdigest()
        else:
            secret_hash = hashlib.md5(password).hexdigest()
            return hashlib.md5('%s-%s' % (salt, secret_hash)).hexdigest()

    def _encode3(self, password, salt=None):  # pragma: py3
        password = bytes(password, 'utf-8')

        if salt is None or salt == '':
            return hashlib.md5(password).hexdigest()
        else:
            secret_hash = hashlib.md5(password).hexdigest()
            message = bytes('%s-%s' % (salt, secret_hash), 'utf-8')
            return hashlib.md5(message).hexdigest()

    def verify(self, password, encoded):
        algorithm, salt, hash = encoded.split('$', 3)
        if len(salt) == 0:
            return constant_time_compare(encoded, self.encode(password, None))
        else:
            return constant_time_compare(encoded, self.encode(password, salt))

    def safe_summary(self, encoded):  # pragma: no cover
        algorithm, salt, hash = encoded.split('$', 3)
        assert algorithm == self.algorithm
        return SortedDict([
            ('algorithm', algorithm),
            ('salt', mask_hash(salt)),
            ('hash', mask_hash(hash)),
        ])

    if six.PY3:  # pragma: py3
        _encode = _encode3
    else:  # pragma: py2
        _encode = _encode2


class PasslibHasher(BasePasswordHasher):
    """Base class for all passlib-based hashers."""
    library = "passlib.hash"


class PhpassHasher(PasslibHasher):
    """Hasher that understands hashes as created by `phpass
    <http://www.openwall.com/phpass/>`_, the "portable PHP password hashing
    framework". This system is most prominently used by `WordPress
    <http://wordpress.org>`_ and `phpBB3 <https://www.phpbb.com/>`_.

    If you want to import hashes created by phpass, just prefix them
    with the string ``phpass``. For example, in PHP, do:

    .. code-block:: php

       $exported_hash = "phpass" . $rawhash;
    """

    algorithm = 'phpass'

    # output of _password_itoa64
    # http://api.drupal.org/api/drupal/includes%21password.inc/function/_password_itoa64/7
    itoa64 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    def __init__(self):
        self.mod = self._load_library().phpass

    def salt(self):  # don't generate a salt, let passlib do it
        return None

    def encode(self, password, salt, rounds=None):
        if salt and len(salt) == 9:
            rounds = self.itoa64.index(salt[0])
            salt = salt[1:]
        return '%s%s' % (self.algorithm, self.mod.encrypt(password, salt=salt, rounds=rounds))

    def verify(self, password, encoded):
        algorithm, hash = encoded.split('$', 1)
        return self.mod.verify(password, '$%s' % hash)


class Drupal7Hasher(PhpassHasher):
    """Hasher that understands hashes as created by Drupal7.

    If you want to import hashes created by Drupal7, just prefix them
    with the string ``drupal7``. For example, in PHP do:

    .. code-block:: php

       $exported_hash = "drupal7" . $rawhash;

    This class is only a slightly modified version of the
    :py:class:`~PhpassHasher`. This class uses Sha512 and hashes start with
    ``$S$`` instead of ``$P$``.

    .. TODO:: Drupal7 supports normal phpass hashes as well, so this module should to.
    """
    algorithm = 'drupal7'

    def __init__(self):  # load hashers loads without constructors
        passlib = self._load_library()
        from passlib.utils import h64
        from passlib.utils.compat import unicode

        class Drupal7Handler(passlib.phpass):
            default_ident = "$S$"
            ident_values = ["$S$", ]
            ident_aliases = {'S': '$S$', }
            default_rounds = 15

            def _calc_checksum(self, secret):
                # FIXME: can't find definitive policy on how phpass handles non-ascii.
                if isinstance(secret, unicode):
                    secret = secret.encode("utf-8")
                real_rounds = 1<<self.rounds
                result = hashlib.sha512(self.salt.encode("ascii") + secret).digest()
                r = 0
                while r < real_rounds:
                    result = hashlib.sha512(result + secret).digest()
                    r += 1
                return h64.encode_bytes(result).decode("ascii")
        self.mod = Drupal7Handler

    def encode(self, password, salt, rounds=None):
        return super(Drupal7Hasher, self).encode(password, salt, rounds=rounds)[:62]

    def verify(self, password, encoded):
        algorithm, hash = encoded.split('$', 1)
        rounds = self.itoa64.index(hash[2])
        salt = hash[3:11]
        generated = self.encode(password, salt=salt, rounds=rounds)

        return constant_time_compare(generated, encoded)


class Apr1Hasher(PasslibHasher):
    """
    Returns hashes using a modified md5 algorithm used by the Apache webserver
    to store passwords. Hashes generated using this function are identical to
    the ones generated with ``htpasswd -m``.
    """
    algorithm = 'apr1'

    def salt(self):
        return None

    def verify(self, password, encoded):
        return self._load_library().apr_md5_crypt.verify(password, '$%s' % encoded)

    def encode(self, password, salt=None):
        return self._load_library().apr_md5_crypt.encrypt(password, salt=salt)[1:]
