#!/usr/bin/python

import sys, MySQLdb, getpass
from optparse import OptionParser

description = """This script is able to read a MySQL database of a MediaWiki and
output appropriate INSERT statements for a RestAuth MySQL database. This script
can also be used as an example if you have a different database at either the
MediaWiki or the RestAuth side."""
usage="%prog [options] --db=database"
parser = OptionParser( description=description, usage=usage )
parser.add_option( '-u', '--user', default='root', help="""The user to use when
connecting to the MySQL server. [default: %default]""" )
parser.add_option( '-p', '--password', metavar='PWD', help="""The password to use
when connecting to the MySQL server. [default: %default]""" )
parser.add_option( '--host', default='localhost',
	help="Connect to MySQL server running on HOST. [default: %default]" )
parser.add_option( '--port', default=3306, type='int',
	help="Use PORT to connect to MySQL server. [default: %default]" )
parser.add_option( '--db', '--database', help="Database to use." )
parser.add_option( '--mediawiki-group', 
	help="Only output users in the specified group." )
opts, args = parser.parse_args()

if not opts.password:
	opts.password = getpass.getpass( 'password: ' )
if not opts.db:
	print( "Error: You must give a Database using --database." )
	sys.exit(1)

query = 'SELECT user_name, user_password, user_registration, user_touched FROM user'
if opts.mediawiki_group:
	query += ', user_groups WHERE user_id = ug_user AND ug_group = "%s"'%opts.mediawiki_group

try:
	db = MySQLdb.connect( opts.host, opts.user, opts.password, opts.db )
	c = db.cursor()

	c.execute( query )
	results = c.fetchall()
except Exception, e:
	print( "Error connecting to database:" )
	print( e )
	sys.exit(1)

records = {}
table = 'Users_serviceuser'
for record in results:
	name, raw_hash, created, touched = record
	name = name.lower()
	if name in records:
		print( "# WARNING: %s exists more than once after case normalization!"%(name) )
	
	records[name] = ( raw_hash, created, touched )

for name, data in records.iteritems():
	raw_hash, created, touched = data

	if raw_hash.startswith( ':B:' ):
		salt, hash = raw_hash.split(':')[2:]
		fields = 'username, algorithm, salt, hash, last_login, date_joined'
		values = "'%s', 'mediawiki', '%s', '%s', '%s', '%s'"%(name, salt, hash, touched, created)
	else:
		hash = raw_hash.split(':')[1:]
		fields = 'username, algorithm, hash, last_login, date_joined'
		values = "'%s', 'mediawiki', '%s', '%s', '%s'"%(name, hash, touched, created)
		
	sql = "INSERT IGNORE INTO %s ( %s ) VALUES ( %s );"%( table, fields, values )
	print( sql )

# TODO: add groups, user properties
