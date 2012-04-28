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

from django.conf import settings
import hashlib, crypt as cryptlib

def crypt_apr1_md5(plainpasswd, salt):
    """
    This function creates an md5 hash that is identical to one that would be created by
    :py:cmd:`htpasswd -m`.
    
    Algorithm shamelessly copied from here:
        http://www.php.net/manual/de/function.crypt.php#73619
    """
    import struct, base64, string
    def pack(val):
        md5 = hashlib.md5(val).hexdigest()
        return struct.pack('16B', *[int(c, 16) for c in (md5[i:i+2] for i in xrange(0, len(md5), 2))])
    
    length = len(plainpasswd)
    text = "%s$apr1$%s"%(plainpasswd, salt)
    md5 = hashlib.md5("%s%s%s"%(plainpasswd, salt, plainpasswd)).hexdigest()
    bin = pack("%s%s%s"%(plainpasswd, salt, plainpasswd))
    
    # first loop
    i = len(plainpasswd)
    while i > 0:
        text += bin[0:min(16,i)]
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
    bin = pack(text)
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

        bin = pack(new)

    tmp = ''
    for i in range(0, 5):
        k = i+6
        j = i+12
        if j == 16:
            j = 5
            
        tmp = "%s%s%s%s"%(bin[i], bin[k], bin[j], tmp)

    tmp = "%s%s%s%s"%(chr(0), chr(0), bin[11], tmp)
    
    frm = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    to = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    trans = string.maketrans(frm, to)
    return base64.b64encode(tmp)[2:][::-1].translate(trans)
            
def mediawiki(secret, salt=None):
    """
    Returns hashes as stored in a `MediaWiki <https://www.mediawiki.org>`_ user database. If salt is
    a string, the hash returned is the md5 hash of a concatenation of the salt, a dash ("-"), and
    the md5 hash of the password, otherwise it is identical to a plain md5 hash of the password.
    
    Please see the `official documentation
    <http://www.mediawiki.org/wiki/Manual:User_table#user_password>`_ for exact details. 
    """
    if salt:
        secret_hash = hashlib.md5(secret).hexdigest()
        return hashlib.md5('%s-%s'%(salt, secret_hash)).hexdigest()
    else: # pragma: no cover
        return hashlib.md5(hash).hexdigest()
        
def crypt(secret, salt=None):
    """
    Returns hashes as generated using the systems `crypt(3)` routine. Hashes like this are used
    by linux system accounts and the ``htpasswd`` tool of the Apache webserver if you used the
    ``-d`` option.
    
    The difference to the implementation shipping with python is that this function automatically
    filters the salt from the returned hash, which is included in the standard version.
    """
    if not salt: # pragma: no cover
        return cryptlib.crypt(secret)
    elif '$' in salt: # pragma: no cover
        # linux system accounts:
        return cryptlib.crypt(secret, salt).rsplit('$', 1)[1]
    else:
        return cryptlib.crypt(secret, salt)[2:]

def apr1(secret, salt=None):
    """
    Returns hashes using a modified md5 algorithm used by the Apache webserver to store passwords.
    Hashes generated using this function are identical to the ones generated with ``htpasswd -m``.
    """
    return crypt_apr1_md5(secret, salt).encode('utf-8')