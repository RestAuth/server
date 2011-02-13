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
import os, time, glob, shutil

def get_version():
	"""
	Dynamically get the current version.
	"""
	version = '0.0' # default
	if os.path.exists( '.version' ): # get from file
		version = open( '.version' ).readlines()[0]
	elif os.path.exists( '.git' ): # get from git
		date = time.strftime( '%Y.%m.%d' )
		cmd = [ 'git', 'rev-parse', '--short', 'HEAD' ]
		p = Popen( cmd, stdout=PIPE )
		stdin = p.communicate()[0].decode( 'utf-8' ).strip()
		version = '%s-%s-%s'%(version, date, stdin )
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

		# remove generated files
		if os.path.exists( 'RestAuth/djangosettings.py' ):
			os.remove( 'RestAuth/djangosettings.py' )
		for filename in glob.glob( 'man/*.[0-9]' ):
			os.remove( filename )

class version( Command ):
	user_options = []
	def initialize_options( self ):
		pass
	def finalize_options( self ):
		pass
	def run( self ):
		print( get_version() )

class build_man( Command ):
	user_options = []
	description = "Build man pages"
	def initialize_options( self ):
		pass
	def finalize_options( self ):
		pass

	def run( self ):
		dictionary = { 
			'__SETTINGS_OPTION__': '''\\fB\-\-settings\\fR=\\fISETTINGS\\fR
.RS 4
The path to the Django settings module. This is equivalent to setting the
environment variable \\fBDJANGO_SETTINGS_MODULE\\fR. \\fISETTINGS\\fR should be the
path to your \\fBsettings.py\\fR. The setting should be in Python path syntax, e.g.
\\fBRestAuth.settings\\fR. The default is usually fine.
.sp
For additinal help, you might want to check out:
.RS 4
\\fIhttp://docs.djangoproject.com/en/dev/topics/settings/\\fR
.sp
.RE
.RE
''' }

		version = get_version()
		date = time.strftime( '%Y-%m-%d' )
		in_files = glob.glob( 'man/*.in' )
		out_files = [ os.path.splitext(e)[0] for e in in_files ]
		man_names = [ os.path.splitext( os.path.basename( e ) ) for e in out_files ]
		data = zip( in_files, out_files, man_names )
		for in_file, out_file, man_name in data:
			name = man_name[0]
			others = [ '\\fB%s\\fR(%s)'%(e[0], e[1].strip('.')) for e in man_names if e != man_name ]
			dictionary['__HEADER__'] = '''.TH %s 8  "%s" "Version %s" "RestAuth Manual"
'''%(name, date, version)
			dictionary['__END__'] = '''.SH ENVIRONMENT
\\fB%s\\fR uses the Django framework and as such is affected by its
environment variables.
.sp
\\fBDJANGO_SETTINGS_MODULE\\fR
.RS 4
Setting this environment variable is equivalent to using the \\fB--settings\\fR
option.
.SH AUTHORS
Copyright \(co 2010\-2011 by RestAuth engineers:
.sp
.RS 4
.ie n \{\h'-04'\(bu\h'+03'\c
.\}
.el \{.sp -1
.IP \(bu 2.3
.\}
Mathias Ertl <mati@fsinf\&.at>
.RE
.sp
License GPLv3+: GNU GPL version 3 or later.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
.sp
See http://gnu.org/licenses/gpl.html for more information.
.SH SEE ALSO
%s
.sp
For more information, see the RestAuth homepage at
.RS 4
\\fIhttps://redmine.fsinf.at/projects/restauth-server\\fR
.RE
.SH BUGS
Please submitt bugs to our issue tracker:
.RS 4
\\fIhttps://redmine.fsinf.at/projects/restauth-server/issues\\fR
'''%(name, ', '.join( others ) )
			process_file( in_file, out_file, dictionary )

class build( _build ):
	def initialize_options( self ):
		"""
		Modify this class so that we also understand --install-dir.
		"""
		_build.initialize_options( self )
		self.prefix = None
		self.exec_prefix = None

	sub_commands = [('build_man', lambda self: True)] + _build.sub_commands
	user_options = _build.user_options + added_options

	def run( self ):
		# generate djangosettings.py
		out_file = 'RestAuth/djangosettings.py'
		if not os.path.exists( out_file ):
			# generate secret key:
			import string, random
			chars = string.letters + string.digits + string.punctuation
			KEY = "".join( [random.choice(chars) for i in xrange(30)] )
			KEY = KEY.replace( '\\', '\\\\' )
			KEY = KEY.replace( '\'', '\\\'' )
			KEY = KEY.replace( '/', '\/' )
			KEY = KEY.replace( '&', '\&' )

			in_file = 'RestAuth/djangosettings.py.in'
			dictionary = { '__SECRET_KEY__': KEY }
			process_file( in_file, out_file, dictionary )
		
		_build.run( self )

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
		'clean': clean, 'build_man': build_man },
)
