# This file is part of RestAuth (http://fs.fsinf.at/wiki/RestAuth).
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

import re, stringprep

def xmpp( name ):
	"""
	Check if the given name is a valid XMPP name. This filters unwanted
	ASCII characters ("&'\/<>@) as well as any space (including unicode ones).
	"""

	# :/\ are also illegal, but already filtered by the general check
	illegal_ascii = ['"', '&', '\'', '/', '<', '>', '@' ]
	for char in illegal_ascii:
		if char in name:
			return False

	# filter unallowed utf-8 characters:
	for char in name:
		enc_char = char.decode( 'utf-8' )
		if stringprep.in_table_c11_c12( enc_char ):
			# various whitespace characters
			return False

	return True

def email( name ):
	"""
	Check if the given name is a valid email adress. Note that email
	adresses MUST be ASCII characters, so if this validator is used, you can
	only use ASCII names.

	Invalid characters in this filter are: (),;<>@[] and any space
	"""
	try:
		name.encode( 'ascii' )
	except UnicodeEncodeError:
		return False

	# :\ are also illegal, but already filtered by the general check
	regex = '[\\s(),;<>@\\[\\]]'
	if re.search( regex, name ):
		return False

	return True

def mediawiki( name ):
	"""
	Filter invalid MediaWiki usernames. This filters names with a
	byte length of more than 255 characters, some reserved names and
	the invalid characters: #<>|[]{}.
	"""
	if len( name.encode('utf-8') ) > 255:
		# Page titles only up to 255 bytes:
		return False

	# already filtered by general check:
	#if name == '.' or name == '..':
	#	return False
	#if name.startswith( "./" ) or name.startswith( "../" ):
	#	return False
	#if name.endswith( "/." ) or name.startswith( "/.." ):
	#	return False

	# see http://www.mediawiki.org/wiki/Manual:$wgReservedUsernames
	reserved_names = [ 'MediaWiki default', 'Conversion script', 
		'Maintenance script', 'msg:double-redirect-fixer',
		'Template namespace initialisation script' ]
	if name in reserved_names:
		return False
	
	regex = '[#<>\\]\\|\\[{}]'
	if re.search( regex, name ):
		return False

	return True

def linux( name ):
	if name.startswith( '-' ):
		return False
	if len( name ) > 32:
		return False

	if re.search( '\s', name ):
		return False

	from RestAuth.common import get_setting
	filter_not_recommended = get_setting( 'FILTER_LINUX_USERNAME_NOT_RECOMMENDED', True )
	
	# filter names that are not recommended:
	if filter_not_recommended and not re.match( '[a-z_][a-z0-9_-]*[$]?', name ):
		return False

	return True

def windows( name ):
	# Reserved names in Windows, see
	# 	http://support.microsoft.com/kb/909264
	reserved = [ 'ANONYMOUS', 'AUTHENTICATED USER', 'BATCH', 'BUILTIN',
		'CREATOR GROUP', 'CREATOR GROUP SERVER', 'CREATOR OWNER', 
		'CREATOR OWNER SERVER', 'DIALUP', 'DIGEST AUTH', 'INTERACTIVE', 
		'INTERNET', 'LOCAL', 'LOCAL SYSTEM', 'NETWORK', 
		'NETWORK SERVICE', 'NT AUTHORITY', 'NT DOMAIN', 'NTLM AUTH',
		'NULL', 'PROXY', 'REMOTE INTERACTIVE', 'RESTRICTED', 
		'SCHANNEL AUTH', 'SELF', 'SERVER', 'SERVICE', 'SYSTEM', 
		'TERMINAL SERVER', 'THIS ORGANIZATION', 'USERS', 'WORLD' ]
	if name in reserved:
		return False
	# :/\ are also illegal, but already filtered by the general check
	illegal = ['"', '[', ']', ';', '|', '=', '+', '*', '?',	'<', '>' ]
	for char in illegal:
		if char in name:
			return False
	return True
