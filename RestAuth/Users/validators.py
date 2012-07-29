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

import re
import stringprep
from RestAuth.common.errors import UsernameInvalid

from django.conf import settings


class validator(object):
    ILLEGAL_CHARACTERS = set()
    """A set of characters that are forbidden on this system. By default, no
    characters are forbidden."""

    ALLOW_WHITESPACE = True
    """If this system allows whitespace. The default is ``True``."""

    FORCE_ASCII = False
    """If this system requires usernames to contain only ASCII characters. The
    default is ``False``."""

    RESERVED = set()
    """A set of reserved usernames. By default, no usernames are reserved."""


class xmpp(validator):
    """
    This validator ensures that usernames are valid username-parts for
    Jabber/XMPP accounts. You can use this validator if you want to provide
    XMPP-addresses of the form ``<username>@example.com``.

    This validator applies the following restrictions:

    * It does not allow any whitespace characters (i.e. space, tab, etc.)
    * The following characters are forbidden: ``"``, ``&`, ``\'``, ``<``, ``>``
      and ``@``
    """
    ILLEGAL_CHARACTERS = set(['"', '&', '\'', '<', '>', '@'])
    ALLOW_WHITESPACE = False


class email(validator):
    """
    This validator ensures that usernames are valid username-parts of
    email-addresses. You can use this validator if you want to provide
    email-addresses of the form ``<username>@example.com``.

    This validator applies the following restrictions:

    * All characters must be ASCII characters.
    * The following ASCII characters are forbidden: ``(``, ``)``, ``,``, ``;``,
      ``<``, ``>``, ``@``, ``[`` and ``]``
    * No spaces are allowed
    * Usernames must not be longer than 64 characters.

    A good reference for valid email addresses is
    `WikiPedia <http://en.wikipedia.org/wiki/Email_address#Syntax>`_.
    """
    ILLEGAL_CHARACTERS = set(['(', ')', ',', ';', '<', '>', '@', '[', ']'])
    ALLOWS_WHITESPACE = False
    FORCE_ASCII = True

    @classmethod
    def check(cls, name):
        if len(name) > 64:
            raise UsernameInvalid(
                "Username must be no longer than 64 characters.")


class mediawiki(validator):
    """
    This validator ensures that usernames are compatible with
    `MediaWiki <http://www.mediawiki.org>`_.

    This validator applies the following restrictions:

    * Usernames must not be longer than 255 **bytes**. An UTF-8 character may
      have more than one byte, so the maximum username length is dependent on
      the characters used.
    * The following ASCII characters are forbidden: ``#``, ``<``, ``>``, ``|``,
      ``[``, ``]``, and ``{}``
    * The following usernames are reserved by MediaWiki and are thus blocked:
      ``mediawiki default``, ``conversion script``, ``maintenance script``,
      ``msg:double-redirect-fixer`` and ``template namespace initialisation
      script``

    See also: `Manual:$wgReservedUsernames
    <http://www.mediawiki.org/wiki/Manual:$wgReservedUsernames>`_
    """
    ILLEGAL_CHARACTERS = set(['#', '<', '>', ']', '|', '[', '{', '}'])
    RESERVED = set([
        'mediawiki default', 'conversion script', 'maintenance script',
        'msg:double-redirect-fixer', 'template namespace initialisation script'
    ])

    @classmethod
    def check(cls, name):
        if len(name.encode('utf-8')) > 255:  # pragma: no cover
            # Page titles only up to 255 bytes:
            raise UsernameInvalid(
                "Username must not be longer than 255 characters")


class linux(validator):
    """
    This validator ensures that usernames are Linux system users.

    This validator applies the following restrictions:

    * All characters must be ASCII characters
    * Usernames must not be longer than 32 characters
    * Usernames must not start with a dash (``-``)

    Unless you set :setting:`RELAXED_LINUX_CHECKS` to ``True``, the following
    additional restrictions apply:

    * Usernames must start with a letter or an underscore (``_``)
    * Usernames may consist only of letters, digits, underscores (``_``) and
      dashes (``-``)
    """

    FORCE_ASCII = True
    ALLOW_WHITESPACE = False

    @  classmethod
    def check(cls, name):
        if name.startswith('-'):
            raise UsernameInvalid(
                '%s: Username must not start with a dash ("-")' % name)
        if len(name) > 32:
            raise UsernameInvalid(
                '%s: Username must not be longer than 32 characters' % name)
        if not settings.RELAXED_LINUX_CHECKS and \
                not re.match('[a-z_ ][a-z0-9_-]*[$]?', name):
            raise UsernameInvalid(
                '%s: Username must match regex "[a-z_][a-z0-9_-]*[$]?"' % name)


class windows(validator):
    """
    This validator ensures that usernames are valid Windows system users.

    .. WARNING:: This validator is completely untested as no Windows systems
       are available. This means that this validator is likely not allow some
       accounts that are in fact not valid. If you can, please consider to
       :ref:`contributing <contribute-validators>`.

    This validator applies the following restrictions:

    * All characters must be ASCII characters
    * The following characters are forbidden: ``"``, ``[``, ``]``, ``;``,
      ``|``, ``=``, ``+``, ``*``, ``?``, ``<`` and ``>``
    * The following usernames are reserved and thus blocked:
      ``anonymous``, ``authenticated user``, ``batch``, ``builtin``,
      ``creator group``, ``creator group server``, ``creator owner``,
      ``creator owner server``, ``dialup``, ``digest auth``, ``interactive``,
      ``internet``, ``local``, ``local system``, ``network``,
      ``network service``, ``nt authority``, ``nt domain``, ``ntlm auth``,
      ``null``, ``proxy``, ``remote interactive``, ``restricted``,
      ``schannel auth``, ``self``, ``server``, ``service``, ``system``,
      ``terminal server``, ``this organization``, ``users`` and ``world``

    For a list of reserved windows usernames, see `this KnowledgeBase article
    <http://support.microsoft.com/kb/909264>`_.
    """
    ILLEGAL_CHARACTERS = set([
        '"', '[', ']', ';', '|', '=', '+', '*', '?', '<', '>'
    ])
    FORCE_ASCII = True
    RESERVED = set([
        'anonymous', 'authenticated user', 'batch', 'builtin', 'creator group',
        'creator group server', 'creator owner', 'creator owner server',
        'dialup', 'digest auth', 'interactive', 'internet', 'local',
        'local system', 'network', 'network service', 'nt authority',
        'nt domain', 'ntlm auth', 'null', 'proxy', 'remote interactive',
        'restricted', 'schannel auth', 'self', 'server', 'service', 'system',
        'terminal server', 'this organization', 'users', 'world',
    ])


class drupal(validator):
    """
    This validator ensures that usernames are valid
    `Drupal <https://drupal.or>`_ usernames.

    This validator applies the following restrictions:

    * Usernames must not start or end with a space or contain multiple spaces
      in a row
    * Various special characters (see Warning)

    .. WARNING:: The function is more or less a direct copy of
       `user_validate_name
       <http://api.drupal.org/api/drupal/modules--user--user.module/function/user_validate_name/7>`_.
       Unlike the Drupal function, the regular expressions actually work and
       filter a wide range of weird characters. For example, 'ä' and 'ö' are
       allowed, while 'ü' is not. It is thus not advisable to use this
       validator at this moment.
    """
    @classmethod
    def check(cls, name):
        if name[0] == ' ':
            raise UsernameInvalid("Username cannot start with a space")
        if name[-1] == ' ':
            raise UsernameInvalid("Username cannot end with a space")
        if '  ' in name:
            raise UsernameInvalid(
                'Username cannot contain multiple spaces in a row')

        if re.match(u'[^\u0080-\u00F7 a-z0-9@_.\'-]', name, re.IGNORECASE):
            raise UsernameInvalid("Username contains an illegal character")
        if re.match(u'[%s%s%s%s%s%s%s%s%s]' % (
                # \x{80}-\x{A0}     // Non-printable ISO-8859-1 + NBSP
                u'\u0080-\u00A0',
                # \x{AD}            // Soft-hyphen
                u'\u00AD',
                # \x{2000}-\x{200F} // Various space characters
                u'\u2000-\u200F',
                # \x{2028}-\x{202F} // Bidirectional text overrides
                u'\u2028-\u202F',
                # \x{205F}-\x{206F} // Various text hinting characters
                u'\u205F-\u206F',
                # \x{FEFF}          // Byte order mark
                u'\uFEFF',
                # \x{FF01}-\x{FF60} // Full-width latin
                u'\uFF01-\uFF60',
                # \x{FFF9}-\x{FFFD} // Replacement characters
                u'\uFFF9-\uFFFD',
                # \x{0}-\x{1F}]  // NULL byte and control characters
                u'\u0000-\u001f'),
                name, re.UNICODE):
            raise UsernameInvalid("Username contains an illegal character")

        # we do not enforce a maximum length, since this is configurable in
        # drupal
