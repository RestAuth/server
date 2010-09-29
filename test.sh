#!/bin/bash

set -e
export RESTAUTH_BASE="$HOME/fs/RestAuth"
export RESTAUTH_PATH="$RESTAUTH_BASE/RestAuth"
export RESTAUTH_BIN="$RESTAUTH_BASE/bin"
export RESTAUTH_DB="$HOME/.RestAuth.sqlite3"

rm -f $RESTAUTH_DB
python manage.py syncdb --noinput
$RESTAUTH_BIN/restauth-service.py --password=vowi add vowi 127.0.0.1
python manage.py runserver
