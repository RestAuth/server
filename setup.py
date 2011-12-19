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

from subprocess import Popen, PIPE
from distutils.core import setup, Command
from distutils.command.install_data import install_data as _install_data
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean
import re, os, sys, time, glob, shutil, argparse

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
	os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'

LATEST_RELEASE = '0.5.2'

if os.path.exists( 'RestAuth' ):
	sys.path.insert( 0, 'RestAuth' )
	
common_path = os.path.join( '..', 'restauth-common', 'python' )
if os.path.exists( common_path ):
	sys.path.insert( 0, common_path )
	pythonpath = os.environ.get( 'PYTHONPATH' )
	if pythonpath:
		os.environ['PYTHONPATH'] += ':%s'%common_path
	else:
		os.environ['PYTHONPATH'] = common_path

def get_version():
	"""
	Dynamically get the current version.
	"""
	version = LATEST_RELEASE # default
	if os.path.exists( '.version' ): # get from file
		version = open( '.version' ).readlines()[0]
	elif os.path.exists( '.git' ): # get from git
		date = time.strftime( '%Y.%m.%d' )
		cmd = [ 'git', 'describe' ]
		p = Popen( cmd, stdout=PIPE )
		version = p.communicate()[0].decode( 'utf-8' )
	elif os.path.exists( 'debian/changelog' ): # building .deb
		f = open( 'debian/changelog' )
		version = re.search( '\((.*)\)', f.readline() ).group(1)
		f.close()
		
		if ':' in version: # strip epoch:
			version = version.split( ':', 1 )[1]
		version = version.rsplit( '-', 1 )[0] # strip debian revision
	return version.strip()

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
		
		if os.path.exists(os.path.join( 'doc', 'coverage')):
			shutil.rmtree(os.path.join('doc', 'coverage'))
		if os.path.exists('MANIFEST'):
			os.remove('MANIFEST')

class version( Command ):
	user_options = []
	def initialize_options( self ):
		pass
	def finalize_options( self ):
		pass
	def run( self ):
		print( get_version() )

class build_doc_meta( Command ):
	def __init__(self, *args, **kwargs ):
		Command.__init__( self, *args, **kwargs )
		
		# generate files for cli-scripts:
		from RestAuth.common import cli
		cli.service_parser.prog = 'restauth-service'
		cli.user_parser.prog = 'restauth-user'
		cli.group_parser.prog = 'restauth-group'
		cli.import_parser.prog = 'restauth-import'
		
		# create necesarry folders:
		if not os.path.exists( 'doc/_static' ):
			os.mkdir( 'doc/_static' )
		if not os.path.exists( 'doc/gen' ):
			os.mkdir( 'doc/gen' )

		for parser, name in [ (cli.service_parser, 'restauth-service'),
				(cli.user_parser, 'restauth-user'),
				(cli.group_parser, 'restauth-group'),
				(cli.import_parser, 'restauth-import') ]:
			
			if self.should_generate( cli.__file__, 'doc/gen/%s-usage.rst'%name ):
				cli.write_usage( parser, 'doc/gen/%s-usage.rst'%name )
			if self.should_generate( cli.__file__, 'doc/gen/%s-commands.rst'%name ):
				cli.write_commands( parser, 'doc/gen/%s-commands.rst'%name, name )
			if self.should_generate( cli.__file__, 'doc/gen/%s-parameters.rst'%name ):
				cli.write_parameters( parser, 'doc/gen/%s-parameters.rst'%name, name )
				
		pythonpath = os.environ.get('PYTHONPATH')
		if pythonpath:
			os.environ['PYTHONPATH'] += ':.'
		else:
			os.environ['PYTHONPATH'] = '.'
		common_path = os.path.join( '..', 'restauth-common', 'python' )
		if os.path.exists( common_path ):
			os.environ['PYTHONPATH'] += ':%s'%(os.path.join('..', common_path))
		
		version = get_version()
		os.environ['SPHINXOPTS'] = '-D release=%s -D version=%s'%(version, version)
		os.environ['RESTAUTH_LATEST_RELEASE'] = LATEST_RELEASE
		
	def should_generate( self, source, generated ):
		if not os.path.exists( generated ):
			return True
		if os.stat( source ).st_mtime > os.stat( generated ).st_mtime:
			return True
		return False
	
	def initialize_options( self ):
		pass
	def finalize_options( self ):
		pass
	user_options = []

class build_doc( build_doc_meta ):
	user_options = []
	description = "Build entire documentation"

	def run( self ):
		cmd = [ 'make', '-C', 'doc', 'man', 'html' ]
		p = Popen( cmd )
		p.communicate()

class build_html( build_doc_meta ):
	user_options = []
	description = "Build HTML documentation"
	def run( self ):
		cmd = [ 'make', '-C', 'doc', 'html' ]
		p = Popen( cmd )
		p.communicate()
		
class build_man( build_doc_meta ):
	user_options = []
	description = "Build man-pages"
	def run( self ):
		cmd = [ 'make', '-C', 'doc', 'man' ]
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

	sub_commands = [('build_man', lambda self: True), ('build_man', lambda self: True)] + _build.sub_commands
	user_options = _build.user_options + added_options

class test( Command ):
	user_options = []
	def initialize_options( self ):
		pass
	def finalize_options( self ):
		pass
	def run( self ):
		from django.core.management import call_command
		call_command( 'test', 'Users', 'Groups', 'Test', 'Services', 'common' )

class coverage( Command ):
	description = "Run test suite and generate code coverage analysis."
	user_options = [
		( 'output-dir=', 'o', 'Output directory for coverage analysis' ),
		( 'user=', 'u', 'Username to use vor RestAuth server' ),
		( 'password=', 'p', 'Password to use vor RestAuth server' ),
		( 'host=', 'h', 'URL of the RestAuth server (ex: http://auth.example.com)') ]
	

	def initialize_options( self ): 
		self.user = 'vowi'
		self.passwd = 'vowi'
		self.host = 'http://[::1]:8000'
		self.dir = 'doc/coverage'

	def finalize_options( self ): pass


	def run( self ):	
		try:
			import coverage
		except ImportError:
			print( "You need coverage.py installed." )
			return

		if not os.path.exists( self.dir ):
			os.makedirs( self.dir )

		cov = coverage.coverage( cover_pylib=False, include='RestAuth/*',
					omit=['*tests.py', '*testdata.py', '*settings.py'] )
		cov.start()
		
		from django.core.management import call_command
		call_command( 'test', 'Users', 'Groups', 'Test', 'Services', 'common' )
		
		cov.stop()
		cov.html_report( directory=self.dir )
#		cov.report()

setup(
	name='RestAuth',
	version=str(get_version()),
	description='RestAuth web service',
	author='Mathias Ertl',
	author_email='mati@restauth.net',
	url='https://restauth.net',
	packages=['RestAuth', 'RestAuth.Services', 'RestAuth.common', 'RestAuth.Groups', 'RestAuth.Users', 'RestAuth.Test' ],
#	scripts = [ 'bin/restauth-groups.py' ],
	data_files = [
		('share/restauth', [ 'wsgi' ] ),
		('share/doc/restauth', ['AUTHORS', 'COPYING', 'COPYRIGHT' ] ),
		],
	cmdclass={
		'install_data': install_data, 'version': version, 'clean': clean,
		'build': build, 'build_doc': build_doc, 'build_man': build_man, 'build_html': build_html,
		'test': test, 'coverage': coverage },
)
