#!/usr/bin/python

import MySQLdb, getpass
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
opts, args = parser.parse_args()

if not opts.password:
	opts.password = getpass.getpass( 'password: ' )

db = MySQLdb.connect( host=opts.host, user=opts.user, passwd=opts.password, db=opts.db )
c = db.cursor()

c.execute( """SELECT user_name, user_password, user_registration, user_touched FROM user""" )
results = c.fetchall()
for record in results:
	name, raw_hash, created, touched = record
	name = name.lower()

	if raw_hash.startswith( ':B:' ):
		salt, hash = raw_hash.split(':')[2:]
		sql = "INSERT INTO Users_serviceuser ( username, algorithm, salt, hash, last_login, date_joined ) VALUES ( '%s', 'mediawiki', '%s', '%s', '%s', '%s' )"%(name, salt, hash, touched, created)
		print( sql )
	else:
		hash = raw_hash.split(':')[1:]
		salt = None

# host, port, user, password, database
