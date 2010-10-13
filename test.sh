#!/bin/bash

export PYTHONPATH="$PWD"

rm -f ./RestAuth.sqlite3
python RestAuth/manage.py syncdb --noinput
../bin/restauth-service.py --password=vowi add vowi 127.0.0.1
python RestAuth/manage.py runserver
