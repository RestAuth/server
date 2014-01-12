# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals  # unicode literals from python

import re

from django.conf import settings
from django.utils import six

from common.errors import UsernameInvalid
from common.utils import import_path

USERNAME_VALIDATORS = None
USERNAME_ILLEGAL_CHARS = set()
USERNAME_RESERVED = set()
USERNAME_FORCE_ASCII = False
USERNAME_NO_WHITESPACE = False


def load_username_validators(validators=None):
    global USERNAME_VALIDATORS
    global USERNAME_ILLEGAL_CHARS
    global USERNAME_RESERVED
    global USERNAME_FORCE_ASCII
    global USERNAME_NO_WHITESPACE

    if validators is None:
        validators = settings.VALIDATORS

    used_validators = []
    illegal_chars = set()
    reserved = set()
    force_ascii = False
    allow_whitespace = True

    for validator_path in validators:
        validator = import_path(validator_path)[0]

        if hasattr(validator, 'check'):
            used_validators.append(validator())

        illegal_chars |= validator.ILLEGAL_CHARACTERS
        reserved |= validator.RESERVED
        if validator.FORCE_ASCII:
            force_ascii = True
        if not validator.ALLOW_WHITESPACE:
            allow_whitespace = False

    USERNAME_FORCE_ASCII = force_ascii
    # use different regular expressions, depending on if we force ASCII
    if not allow_whitespace:
        if force_ascii:
            USERNAME_NO_WHITESPACE = re.compile('\s')
        else:
            USERNAME_NO_WHITESPACE = re.compile('\s', re.UNICODE)
    else:
        USERNAME_NO_WHITESPACE = False

    USERNAME_RESERVED = reserved
    USERNAME_ILLEGAL_CHARS = illegal_chars
    USERNAME_VALIDATORS = used_validators


def validate_username(username):
    if len(username) < settings.MIN_USERNAME_LENGTH:
        raise UsernameInvalid("Username too short")
    if len(username) > settings.MAX_USERNAME_LENGTH:
        raise UsernameInvalid("Username too long")

    if USERNAME_VALIDATORS is None:
        load_username_validators()

    # check for illegal characters:
    for char in USERNAME_ILLEGAL_CHARS:
        if char in username:
            raise UsernameInvalid("Username must not contain character '%s'" % char)

    # reserved names
    if username in USERNAME_RESERVED:
        raise UsernameInvalid("Username is reserved")

    # force ascii if necessary
    if USERNAME_FORCE_ASCII:
        try:
            if six.PY3:  # pragma: py3
                bytes(username, 'ascii')
            else:  # pragma: py2
                username.decode('ascii')
        except (UnicodeDecodeError, UnicodeEncodeError):
            raise UsernameInvalid("Username must only contain ASCII characters")

    # check for whitespace
    if USERNAME_NO_WHITESPACE is not False:
        if USERNAME_NO_WHITESPACE.search(username):
            raise UsernameInvalid("Username must not contain any whitespace")

    for validator in USERNAME_VALIDATORS:
        validator.check(username)


def get_validators():
    if USERNAME_VALIDATORS is None:  # pragma: no cover
        # saveguard, load_username_validators() is always called first.
        load_username_validators()

    return USERNAME_VALIDATORS


class Validator(object):
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


class XMPPValidator(Validator):
    """This validator ensures that usernames are valid username-parts for Jabber/XMPP accounts. You
    can use this validator if you want to provide XMPP-addresses of the form
    ``<username>@example.com``.

    This validator applies the following restrictions:

    * It does not allow any whitespace characters (i.e. space, tab, etc.)
    * The following characters are forbidden: ``"``, ``&`, ``\'``, ``<``, ``>``
      and ``@``
    """
    ILLEGAL_CHARACTERS = set(['"', '&', '\'', '<', '>', '@'])
    ALLOW_WHITESPACE = False


class EmailValidator(Validator):
    """This validator ensures that usernames are valid username-parts of email-addresses. You can
    use this validator if you want to provide email-addresses of the form
    ``<username>@example.com``.

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

    def check(self, name):
        if len(name) > 64:
            raise UsernameInvalid("Username must be no longer than 64 characters.")


class MediaWikiValidator(Validator):
    """This validator ensures that usernames are compatible with
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

    def check(self, name):
        if len(name.encode('utf-8')) > 255:
            # Page titles only up to 255 bytes:
            raise UsernameInvalid("Username must not be longer than 255 characters")


class LinuxValidator(Validator):
    """This validator ensures that usernames are Linux system users.

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

    def check(cls, name):
        if name.startswith('-'):
            raise UsernameInvalid('%s: Username must not start with a dash ("-")' % name)
        if len(name) > 32:
            raise UsernameInvalid('%s: Username must not be longer than 32 characters' % name)

        regex = '[a-z_ ][a-z0-9_-]*[$]?$'
        if not settings.RELAXED_LINUX_CHECKS and not re.match(regex, name):
            raise UsernameInvalid('%s: Username must match regex "%s"' % (name, regex))


class WindowsValidator(Validator):
    """This validator ensures that usernames are valid Windows system users.

    .. WARNING:: This validator is completely untested as no Windows systems are available. This
       means that this validator is likely not allow some accounts that are in fact not valid. If
       you can, please consider to :ref:`contributing <contribute-validators>`.

    This validator applies the following restrictions:

    * All characters must be ASCII characters
    * The following characters are forbidden: ``"``, ``[``, ``]``, ``;``,
      ``|``, ``=``, ``+``, ``*``, ``?``, ``<`` and ``>``
    * The following usernames are reserved and thus blocked: ``anonymous``, ``authenticated user``,
      ``batch``, ``builtin``, ``creator group``, ``creator group server``, ``creator owner``,
      ``creator owner server``, ``dialup``, ``digest auth``, ``interactive``, ``internet``,
      ``local``, ``local system``, ``network``, ``network service``, ``nt authority``,
      ``nt domain``, ``ntlm auth``, ``null``, ``proxy``, ``remote interactive``, ``restricted``,
      ``schannel auth``, ``self``, ``server``, ``service``, ``system``, ``terminal server``,
      ``this organization``, ``users`` and ``world``

    For a list of reserved windows usernames, see `this KnowledgeBase article
    <http://support.microsoft.com/kb/909264>`_.
    """
    ILLEGAL_CHARACTERS = set([
        '"', '[', ']', ';', '|', '=', '+', '*', '?', '<', '>',
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


class DrupalValidator(Validator):
    """This validator ensures that usernames are valid `Drupal <https://drupal.or>`_ usernames.

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
    def check(self, name):
        if name[0] == ' ':
            raise UsernameInvalid("Username cannot start with a space")
        if name[-1] == ' ':
            raise UsernameInvalid("Username cannot end with a space")
        if '  ' in name:
            raise UsernameInvalid('Username cannot contain multiple spaces in a row')

        if re.search('[^\u0080-\u00F7 a-z0-9@_.\'-]', name, re.IGNORECASE):
            raise UsernameInvalid("Username contains an illegal character")
        if re.search('[%s%s%s%s%s%s%s%s%s]' % (
                # \x{80}-\x{A0}     // Non-printable ISO-8859-1 + NBSP
                '\u0080-\u00A0',
                # \x{AD}            // Soft-hyphen
                '\u00AD',
                # \x{2000}-\x{200F} // Various space characters
                '\u2000-\u200F',
                # \x{2028}-\x{202F} // Bidirectional text overrides
                '\u2028-\u202F',
                # \x{205F}-\x{206F} // Various text hinting characters
                '\u205F-\u206F',
                # \x{FEFF}          // Byte order mark
                '\uFEFF',
                # \x{FF01}-\x{FF60} // Full-width latin
                '\uFF01-\uFF60',
                # \x{FFF9}-\x{FFFD} // Replacement characters
                '\uFFF9-\uFFFD',
                # \x{0}-\x{1F}]  // NULL byte and control characters
                '\u0000-\u001f'),
                name, re.UNICODE):  # pragma: no cover
            raise UsernameInvalid("Username contains an illegal character")

        # we do not enforce a maximum length, since this is configurable in
        # drupal
