# This file is part of RestAuthClient.py.
#
#    RestAuthClient.py is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Foobar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RestAuthClient.py.  If not, see <http://www.gnu.org/licenses/>.

from subprocess import Popen, PIPE
from os import listdir
from os.path import normpath, isdir, basename, exists, isfile
from shutil import copytree, ignore_patterns
from distutils.core import setup, Command
from distutils.command.install_data import install_data as _install_data
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean
from distutils.util import execute

class install_data( _install_data ):
	"""
	Improve the install_data command so it can also copy directories
	"""
	def custom_copy_tree( self, src, dest ):
		base = basename( src )
		dest = normpath( "%s/%s/%s"%( self.install_dir, dest, base ) )
		if exists( dest ):
			return
		ignore = ignore_patterns( '.svn', '*.pyc' )
		print( "copying %s -> %s"%(src, dest) )
		copytree( src, dest, ignore=ignore )
		
	def run( self ):
		for dest, nodes in self.data_files:
			dirs = [ node for node in nodes if isdir( node ) ]
			for src in dirs:
				self.custom_copy_tree(src, dest)
				nodes.remove( src )
		_install_data.run( self )

added_options = [('prefix=', None, 'installation prefix'),
	('exec-prefix=', None, 'prefix for platform-specific files'),
	('patch-dir=', None, 'Directory where patches are located.') ]

class patch_command( Command ):
	user_options = added_options
	
	def initialize_options( self ):
		self.prefix = '/usr/local'
		self.exec_prefix = '/usr/local/bin'
		self.patch_dir = 'patches'

	def finalize_options( self ):
		command = self.get_command_name()
		options = self.distribution.command_options[ command ]
		
		if 'prefix' in options:
			self.prefix = options['prefix'][1]
		if 'exec_prefix' in options:
			self.exec_prefix = options['exec_prefix'][1]
		if 'patch_dir' in options:
			self.patch_dir = options['patch_dir'][1]
	
	def run( self ):
		for patch in listdir( self.patch_dir ):
			full_path = normpath( self.patch_dir + '/' + patch )

			if isdir( full_path ):
				continue

			print( " Applying %s..."%(patch) )

			f = open( full_path )
			lines = f.readlines()
			patch_lines = []
			for line in lines:
				line = line.replace( '__PREFIX__', self.prefix )
				patch_lines.append( line )

			patch = "".join( patch_lines )

			# todo: already applied patches
			cmd = [ 'patch' ] + self.__class__.patch_args
			print( ' '.join( cmd ) )
			p = Popen( cmd, stdin=PIPE )
			p.stdin.write( patch )

class patch( patch_command ):
	description = "Patch source code before installation" 
	patch_args = [ '-t', '-p0' ]
	
class unpatch( patch_command ):
	description = "Patch source code before installation"
	patch_args = [ '-R', '-t', '-p0' ]

class build( _build ):
	def has_patches(self):
		if not self.patch_dir or not exists( self.patch_dir ):
			return False

		ls = listdir( self.patch_dir )
		files = [ f for f in ls if isfile( "%s/%s"%(self.patch_dir, f) ) ]
		if files:
			return True

		return False

	def initialize_options( self ):
		"""
		Modify this class so that we also understand --install-dir.
		"""
		_build.initialize_options( self )
		self.prefix = None
		self.exec_prefix = None
		self.patch_dir = None

	sub_commands = [('patch', has_patches)] + _build.sub_commands
	user_options = _build.user_options + added_options

class clean( _clean ):
	def has_patches( self ):
		if not self.patch_dir or not exists( self.patch_dir ):
			return False

		ls = listdir( self.patch_dir )
		files = [ f for f in ls if isfile( "%s/%s"%(self.patch_dir, f) ) ]
		if files:
			return True

		return False

	def initialize_options( self ):
		_clean.initialize_options( self )
		self.patch_dir = None
		
	sub_commands = [('unpatch', has_patches)] + _build.sub_commands
	user_options = _clean.user_options + [ ('patch-dir=', None, 'Directory where patches are located.') ]

def get_version():
	version = '0.1'
	if exists( '.version' ):
		print( 'get version from file...' )
		version = open( '.version' ).readlines()[0]
	elif exists( '.svn' ):
		cmd = [ 'svn', 'info' ]
		p = Popen( cmd, stdout=PIPE )
		stdin, stderr = p.communicate()
		lines = stdin.split( "\n" )
		line = [ line for line in lines if line.startswith( 'Revision' ) ][0]
		version = '0.0-' + line.split( ': ' )[1].strip()
	return version

class version( Command ):
	user_options = []
	def initialize_options( self ):
		pass
	def finalize_options( self ):
		pass
	def run( self ):
		print( get_version() )

setup(
	name='RestAuth',
	version=get_version(),
	description='RestAuth web service',
	author='Mathias Ertl',
	author_email='mati@fsinf.at',
	url='http://fs.fsinf.at/wiki/RestAuth',
	packages=['RestAuth', 'RestAuth.Services', 'RestAuth.common', 'RestAuth.Groups', 'RestAuth.Users' ],
#	scripts = [ 'bin/restauth-groups.py' ],
	data_files = [
		('share/restauth', [ 'wsgi' ] ),
		('share/', ['doc'] ),
		('share/doc/restauth', ['AUTHORS', 'COPYING', 'COPYRIGHT'] ),
		],
	cmdclass={
		'install_data': install_data,
		'build': build, 'version': version,
		'patch': patch, 'unpatch': unpatch },
)
