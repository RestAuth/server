#!/usr/bin/python

import os, shutil
from subprocess import Popen, PIPE

os.chdir( 'debian/restauth' )
p = Popen( ['find', '-type', 'f', '-name', 'settings.py'], stdout=PIPE )
settings_path = p.communicate()[0].strip()
shutil.move( settings_path, 'etc/restauth' )
os.symlink( '/etc/restauth/settings.py', settings_path )

p = Popen( ['find', '-type', 'f', '-name', 'manage.py'], stdout=PIPE )
manage_path = p.communicate()[0].strip().strip('.')
print( manage_path )
os.symlink( manage_path, 'usr/bin/restauth-manage' )
