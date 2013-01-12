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
import string
import struct

from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils.crypto import constant_time_compare, get_random_string
from django.utils.datastructures import SortedDict


class Sha512Hasher(BasePasswordHasher):
    algorithm = 'sha512'

    def encode(self, password, salt):
        hash = hashlib.sha512('%s%s' % (salt, password)).hexdigest()
        return '%s$%s$%s' % (self.algorithm, salt, hash)

    def verify(self, password, encoded):
        algorithm, salt, hash = encoded.split('$', 3)
        return constant_time_compare(encoded, self.encode(password, salt))

    def safe_summary(self, encoded):
        algorithm, salt, hash = encoded.split('$', 3)
        assert algorithm == self.algorithm
        return SortedDict([
            ('algorithm', algorithm),
            ('salt', mask_hash(salt)),
            ('hash', mask_hash(hash)),
        ])

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
        if salt is None:
            salt = ''
            hash = hashlib.md5(hash).hexdigest()
        else:
            secret_hash = hashlib.md5(password).hexdigest()
            hash = hashlib.md5('%s-%s' % (salt, secret_hash)).hexdigest()
        return '%s$%s$%s' % (self.algorithm, salt, hash)

    def verify(self, password, encoded):
        algorithm, salt, hash = encoded.split('$', 3)
        if len(salt) == 0:
            return constant_time_compare(encoded, self.encode(password, None))
        else:
            return constant_time_compare(encoded, self.encode(password, salt))

    def safe_summary(self, encoded):
        algorithm, salt, hash = encoded.split('$', 3)
        assert algorithm == self.algorithm
        return SortedDict([
            ('algorithm', algorithm),
            ('salt', mask_hash(salt)),
            ('hash', mask_hash(hash)),
        ])


class Apr1Hasher(BasePasswordHasher):
    """
    Returns hashes using a modified md5 algorithm used by the Apache webserver
    to store passwords. Hashes generated using this function are identical to
    the ones generated with ``htpasswd -m``.
    """

    algorithm = 'apr1'

    def verify(self, password, encoded):
        algorithm, salt, hash = encoded.split('$', 3)
        new_hash = self._crypt(password, salt)
        return constant_time_compare(hash, new_hash)

    def encode(self, password, salt):
        hash = self._crypt(password, salt).encode('utf-8')
        return '%s$%s$%s' % (self.algorithm, salt, hash)

    def safe_summary(self, encoded):
        algorithm, salt, hash = encoded.split('$', 3)
        assert algorithm == self.algorithm
        return SortedDict([
            ('algorithm', algorithm),
            ('salt', mask_hash(salt)),
            ('hash', mask_hash(hash)),
        ])

    def _pack(self, val):
        md5 = hashlib.md5(val).hexdigest()
        cs = [md5[i:i + 2] for i in xrange(0, len(md5), 2)]
        values = [int(c, 16) for c in cs]
        return struct.pack('16B', *values)

    def _crypt(self, plainpasswd, salt):
        """
        This function creates an md5 hash that is identical to one that would be
        created by :cmd:`htpasswd -m`.

        Algorithm shamelessly copied from here:
            http://www.php.net/manual/de/function.crypt.php#73619
        """
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

        frm = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        to = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        trans = string.maketrans(frm, to)
        return base64.b64encode(tmp)[2:][::-1].translate(trans)
