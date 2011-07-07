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
from distutils.core import setup, Command
from distutils.command.install_data import install_data as _install_data
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean
import re, os, sys, time, glob, shutil, argparse

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
	os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'

def get_version():
	"""
	Dynamically get the current version.
	"""
	version = '0.0' # default
	if os.path.exists( '.version' ): # get from file
		version = open( '.version' ).readlines()[0]
	elif os.path.exists( '.git' ): # get from git
		date = time.strftime( '%Y.%m.%d' )
		cmd = [ 'git', 'describe' ]
		p = Popen( cmd, stdout=PIPE )
		version = p.communicate()[0].decode( 'utf-8' )
	return version.strip()


def process_file( in_path, out_path, dictionary ):
	"""
	Used to dynamically create files. Reads file at in_path, writes it to
	out_path and replaces all occurrences of any key of the dictionary with
	its corresponding value.
	"""
	in_file = open( in_path )
	out_file = open( out_path, 'w' )
	for line in in_file.readlines():
		for key in dictionary.keys():
			if key in line:
				line = line.replace( key, dictionary[key] )
		out_file.write( line )

class install_data( _install_data ):
	"""
	Improve the install_data command so it can also copy directories
	"""
	def custom_copy_tree( self, src, dest ):
		base = os.path.basename( src )
		dest = os.path.normpath( "%s/%s/%s"%( self.install_dir, dest, base ) )
		if os.path.exists( dest ):
			return
		ignore = shutil.ignore_patterns( '.svn', '*.pyc' )
		print( "copying %s -> %s"%(src, dest) )
		shutil.copytree( src, dest, ignore=ignore )
		
	def run( self ):
		for dest, nodes in self.data_files:
			dirs = [ node for node in nodes if os.path.isdir( node ) ]
			for src in dirs:
				self.custom_copy_tree(src, dest)
				nodes.remove( src )
		_install_data.run( self )

added_options = [('prefix=', None, 'installation prefix'),
	('exec-prefix=', None, 'prefix for platform-specific files') ]

class clean( _clean ):
	def initialize_options( self ):
		_clean.initialize_options( self )
		
	def run( self ):
		_clean.run( self )
		
		# clean sphinx documentation:
		cmd = [ 'make', '-C', 'doc', 'clean' ]
		p = Popen( cmd )
		p.communicate()

class version( Command ):
	user_options = []
	def initialize_options( self ):
		pass
	def finalize_options( self ):
		pass
	def run( self ):
		print( get_version() )

class build_doc( Command ):
	user_options = []
	description = "Build documentation"
	def initialize_options( self ):
		pass
	def finalize_options( self ):
		pass

	def run( self ):
		sys.path.insert( 0, 'bin/' )
		from RestAuth.common.cli import service_parser, user_parser, group_parser
		from RestAuth.common.cli import format_man_usage, write_commands, write_usage
		service_parser.prog = 'restauth-service'
		user_parser.prog = 'restauth-user'
		group_parser.prog = 'restauth-group'
		
		write_usage( service_parser, 'restauth-service' )
		write_commands( service_parser, 'restauth-service' )
		
		write_usage( user_parser, 'restauth-user' )
		write_commands( user_parser, 'restauth-user' )
		
		write_usage( group_parser, 'restauth-group' )
		write_commands( group_parser, 'restauth-group' )
		
		if not os.path.exists( 'doc/_static' ):
			os.mkdir( 'doc/_static' )
		if not os.path.exists( 'doc/includes' ):
			os.mkdir( 'doc/includes' )
		os.environ['PYTHONPATH'] = '.'
		cmd = [ 'make', '-C', 'doc', 'clean', 'man', 'html' ]
		p = Popen( cmd )
		p.communicate()

class build( _build ):
	def initialize_options( self ):
		"""
		Modify this class so that we also understand --install-dir.
		"""
		_build.initialize_options( self )
		self.prefix = None
		self.exec_prefix = None

	sub_commands = [('build_doc', lambda self: True)] + _build.sub_commands
	user_options = _build.user_options + added_options

setup(
	name='RestAuth',
	version=get_version(),
	description='RestAuth web service',
	author='Mathias Ertl',
	author_email='mati@fsinf.at',
	url='http://fs.fsinf.at/wiki/RestAuth/RestAuth',
	packages=['RestAuth', 'RestAuth.Services', 'RestAuth.common', 'RestAuth.Groups', 'RestAuth.Users' ],
#	scripts = [ 'bin/restauth-groups.py' ],
	data_files = [
		('share/restauth', [ 'wsgi' ] ),
		('share/doc/restauth', ['AUTHORS', 'COPYING', 'COPYRIGHT', 'doc/migration', 'doc/mod_wsgi'] ),
		],
	cmdclass={
		'install_data': install_data, 'build': build, 'version': version,
		'clean': clean, 'build_doc': build_doc },
)
