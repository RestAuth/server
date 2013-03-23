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

import base64
import hashlib
import math
import string
import struct
import sys

from django.contrib.auth.hashers import BasePasswordHasher
from django.contrib.auth.hashers import mask_hash
from django.utils.crypto import constant_time_compare
from django.utils.crypto import get_random_string
from django.utils.datastructures import SortedDict


if sys.version_info < (3, 0):
    IS_PYTHON3 = False
else:
    IS_PYTHON3 = True


class Sha512Hasher(BasePasswordHasher):
    """A basic sha512 hasher with salt.

    This hasher hashing algorithm that used to be the default before RestAuth
    0.6.1.
    """

    algorithm = 'sha512'

    def _hash2(self, payload):
        return hashlib.sha512(payload).hexdigest()

    def _hash3(self, payload):
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

    if IS_PYTHON3:
        _hash = _hash3
    else:
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

    def _encode2(self, password, salt=None):
        if salt is None:
            return hashlib.md5(password).hexdigest()
        else:
            secret_hash = hashlib.md5(password).hexdigest()
            return hashlib.md5('%s-%s' % (salt, secret_hash)).hexdigest()

    def _encode3(self, password, salt=None):
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

    if IS_PYTHON3:
        _encode = _encode3
    else:
        _encode = _encode2


class PhpassHasher(BasePasswordHasher):
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

    # some constants by PHPass
    MIN_HASH_COUNT = 7
    MAX_HASH_COUNT = 30

    HASH_LENGTH = 55
    HASH_COUNT = 15

    # output of _password_itoa64
    # http://api.drupal.org/api/drupal/includes%21password.inc/function/_password_itoa64/7
    itoa64 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    # works in both python2 and python3
    def salt(self):
        count = self.itoa64[self.HASH_COUNT]
        salt = self._password_base64_encode(get_random_string(6), 6)
        return '%s%s' % (count, salt)

    # works in both python2 and python3
    def _password_enforce_log2_boundaries(self, count_log2):
        """Implementation of _password_enforce_log2_boundaries

        .. seealso:: http://api.drupal.org/api/drupal/includes%21password.inc/function/_password_enforce_log2_boundaries/7
        """
        if count_log2 < self.MIN_HASH_COUNT:
            return self.MIN_HASH_COUNT
        elif count_log2 > self.MAX_HASH_COUNT:
            return self.MAX_HASH_COUNT
        else:
            return count_log2

    def _password_base64_encode(self, input, count):
        """Implementation of _password_base64_encode.

        Equivalent to the ``encode64`` function in phpass.

        .. seealso:: http://api.drupal.org/api/drupal/includes%21password.inc/function/_password_base64_encode/7

        :param input: string to encode
        :type  input: str
        :return:      The encoded string
        :rtype:       str
        """
        output = ''
        i = 0

        while i < count:
            # NOTE: We use these weird indizes for python 3 compatability:
            # in python2:  'foo'[0]   --> 'f'
            # in python3:  'foo'[0]   --> 'f'
            #             b'foo'[0]   --> 102  <-- this breaks ord()
            #             b'foo'[0:1] --> 'f'
            value = ord(input[i:i + 1])
            i += 1

            output += self.itoa64[value & 0x3f]
            if (i < count):
                value |= ord(input[i:i + 1]) << 8

            output += self.itoa64[(value >> 6) & 0x3f]

            if (i >= count):
                break
            i += 1

            if i < count:
                value |= ord(input[i:i + 1]) << 16

            output += self.itoa64[(value >> 12) & 0x3f]
            if (i >= count):
                break
            i += 1

            output += self.itoa64[(value >> 18) & 0x3f]
        return output

    def _compute_hash2(self, hashfunc, count, salt, password):
        hash = hashfunc('%s%s' % (salt, password)).digest()
        for i in range(0, count):
            hash = hashfunc('%s%s' % (hash, password)).digest()
        return hash

    def _compute_hash3(self, hashfunc, count, salt, password):
        salt = bytes(salt, 'utf-8')
        password = bytes(password, 'utf-8')

        hash = hashfunc(salt + password).digest()
        for i in range(0, count):
            hash = hashfunc(hash + password).digest()
        return hash

    def _password_crypt(self, hashfunc, password, setting):
        setting = setting[:12]

        if setting[0] != '$' or setting[2] != '$':
            return False

        count_log2 = self.itoa64.index(setting[3])
        # Hashes may be imported from elsewhere, so we allow != HASH_COUNT
        if count_log2 < self.MIN_HASH_COUNT or count_log2 > self.MAX_HASH_COUNT:
            return False

        salt = setting[4:12]
        # Hashes must have an 8 character salt.
        if len(salt) != 8:
            return False

        # Convert the base 2 logarithm into an integer.
        count = 1 << count_log2

        # We rely on the hash() function being available in PHP 5.2+.
        hash = self._compute_hash(hashfunc, count, salt, password)

        length = len(hash)

        output = '%s%s' % (setting, self._password_base64_encode(hash, length))
        expected = 12 + math.ceil((8 * length) / 6.0)
        if len(output) == expected:
            return output[0:self.HASH_LENGTH]
        else:
            return False

    def verify(self, password, encoded):
        enc_hash = encoded[6:]

        if enc_hash.startswith('$H$') or enc_hash.startswith('$P$'):
            recoded = self._password_crypt(hashlib.md5, password, enc_hash)
        else:
            return False

        if recoded is False:
            return recoded
        else:
            return constant_time_compare(enc_hash, recoded)

    def encode(self, password, salt):
        settings = '$P$%s' % salt
        encoded = self._password_crypt(hashlib.md5, password, settings)
        return '%s%s' % (self.algorithm, encoded)

    if IS_PYTHON3:
        _compute_hash = _compute_hash3
    else:
        _compute_hash = _compute_hash2


class Drupal7Hasher(PhpassHasher):
    """Hasher that understands hashes as created by Drupal7.

    If you want to import hashes created by Drupal7, just prefix them
    with the string ``drupal7``. For example, in PHP do:

    .. code-block:: php

       $exported_hash = "drupal7" . $rawhash;

    This class is only a slightly modified version of the
    :py:class:`~PhpassHasher`. This class uses Sha512 and hashes start with
    ``$S$`` instead of ``$P$``. Like Drupal7, it does support reading normal
    ``$P$`` hashes as well.
    """

    algorithm = 'drupal7'

    def verify(self, password, encoded):
        enc_hash = encoded[7:]

        if enc_hash.startswith('$S$'):
            recoded = self._password_crypt(hashlib.sha512, password, enc_hash)
        elif enc_hash.startswith('$H$') or enc_hash.startswith('$P$'):
            recoded = self._password_crypt(hashlib.md5, password, enc_hash)
        else:
            return False

        if recoded is False:
            return recoded
        else:
            return constant_time_compare(enc_hash, recoded)

    def encode(self, password, salt):
        settings = '$S$%s' % salt
        encoded = self._password_crypt(hashlib.sha512, password, settings)
        return '%s%s' % (self.algorithm, encoded)


class Apr1Hasher(BasePasswordHasher):
    """
    Returns hashes using a modified md5 algorithm used by the Apache webserver
    to store passwords. Hashes generated using this function are identical to
    the ones generated with ``htpasswd -m``.
    """

    algorithm = 'apr1'

    def verify(self, password, encoded):
        algorithm, salt, hash = encoded.split('$', 3)
        newhash = self._crypt(password, salt)
        return constant_time_compare(hash, newhash)

    def encode(self, password, salt):
        hash = self._crypt(password, salt)
        return '%s$%s$%s' % (self.algorithm, salt, hash)

    def safe_summary(self, encoded):  # pragma: no cover
        algorithm, salt, hash = encoded.split('$', 3)
        assert algorithm == self.algorithm
        return SortedDict([
            ('algorithm', algorithm),
            ('salt', mask_hash(salt)),
            ('hash', mask_hash(hash)),
        ])

    def _pack2(self, val):
        md5 = hashlib.md5(val).hexdigest()
        cs = [md5[i:i + 2] for i in xrange(0, len(md5), 2)]
        values = [int(c, 16) for c in cs]
        return struct.pack('16B', *values)

    def _pack3(self, val):
        md5 = hashlib.md5(val).hexdigest()
        cs = [md5[i:i + 2] for i in range(0, len(md5), 2)]
        values = [int(c, 16) for c in cs]
        return struct.pack('16B', *values)

    def _trans2(self, val):
        frm = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        to = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        trans = string.maketrans(frm, to)
        return base64.b64encode(val)[2:][::-1].translate(trans)

    def _trans3(self, val):
        frm = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        to = b"./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        trans = bytes.maketrans(frm, to)
        return base64.b64encode(val)[2:][::-1].translate(trans)

    def _crypt3(self, plainpasswd, salt):
        text = bytes("%s$apr1$%s" % (plainpasswd, salt), 'utf-8')

        to_pack = "%s%s%s" % (plainpasswd, salt, plainpasswd)
        bin = self._pack(bytes(to_pack, 'utf-8'))

        # first loop
        i = len(plainpasswd)
        while i > 0:
            text += bin[0:min(16, i)]
            i -= 16

        # second loop
        i = len(plainpasswd)
        while i > 0:
            if i & 1:
                text += bytes(chr(0), 'utf-8')
            else:
                text += bytes(plainpasswd[0], 'utf-8')

            # shift bits by one (/2 rounded down)
            i >>= 1

        # 1000er loop
        bin = self._pack(text)
        for i in range(0, 1000):
            if i & 1:
                new = bytes(plainpasswd, 'utf-8')
            else:
                new = bin

            if i % 3:
                new += bytes(salt, 'utf-8')
            if i % 7:
                new += bytes(plainpasswd, 'utf-8')

            if i & 1:
                new += bin
            else:
                new += bytes(plainpasswd, 'utf-8')

            bin = self._pack(new)

        tmp = b''
        for i in range(0, 5):
            k = i + 6
            j = i + 12
            if j == 16:
                j = 5

            tmp = "%s%s%s%s" % (chr(bin[i]), chr(bin[k]), chr(bin[j]),
                                tmp.decode('iso-8859-1'))
            tmp = bytes(tmp, 'iso-8859-1')
        tmp = "%s%s%s%s" % (chr(0), chr(0), chr(bin[11]),
                            tmp.decode('iso-8859-1'))
        tmp = bytes(tmp, 'iso-8859-1')

        return self._trans(tmp).decode('utf-8')

    def _crypt2(self, plainpasswd, salt):
        """
        This function creates an md5 hash that is identical to one that would
        be created by :cmd:`htpasswd -m`.

        Algorithm shamelessly copied from here:
            http://www.php.net/manual/de/function.crypt.php#73619
        """
        plainpasswd = str(plainpasswd)
        salt = str(salt)  # unicode in Django 1.5, must be str
        text = "%s$apr1$%s" % (plainpasswd, salt)
        bin = self._pack("%s%s%s" % (plainpasswd, salt, plainpasswd))

        # first loop
        i = len(plainpasswd)
        while i > 0:
            text += bin[0:min(16, i)]
            i -= 16

        # second loop
        i = len(plainpasswd)
        while i > 0:
            if i & 1:
                text += chr(0)
            else:
                text += plainpasswd[0]

            # shift bits by one (/2 rounded down)
            i >>= 1

        # 1000er loop
        bin = self._pack(text)
        for i in range(0, 1000):
            if i & 1:
                new = plainpasswd
            else:
                new = bin

            if i % 3:
                new += salt
            if i % 7:
                new += plainpasswd

            if i & 1:
                new += bin
            else:
                new += plainpasswd

            bin = self._pack(new)

        tmp = ''
        for i in range(0, 5):
            k = i + 6
            j = i + 12
            if j == 16:
                j = 5

            tmp = "%s%s%s%s" % (bin[i], bin[k], bin[j], tmp)

        tmp = "%s%s%s%s" % (chr(0), chr(0), bin[11], tmp)

        return self._trans(tmp).encode('utf-8')

    if IS_PYTHON3:
        _trans = _trans3
        _pack = _pack3
        _crypt = _crypt3
    else:
        _trans = _trans2
        _pack = _pack2
        _crypt = _crypt2
