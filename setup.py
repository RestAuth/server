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

from os.path import normpath, isdir, basename, exists
from shutil import copytree, ignore_patterns
from distutils.core import setup
from distutils.command.install_data import install_data as _install_data
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


setup(
	name='RestAuth',
	version='1.0',
	description='RestAuth web service',
	author='Mathias Ertl',
	author_email='mati@fsinf.at',
	url='http://fs.fsinf.at/wiki/RestAuth',
	packages=['RestAuth', 'RestAuth.Services', 'RestAuth.common', 'RestAuth.Groups', 'RestAuth.Users' ],
	scripts = [ 'bin/restauth-groups.py' ],
	data_files = [
		('share/restauth', [ 'wsgi' ] ),
		('share/', ['doc'] ),
		('share/doc', ['AUTHORS', 'COPYING', 'COPYRIGHT'] ),
		],
	cmdclass={'install_data': install_data}
)
