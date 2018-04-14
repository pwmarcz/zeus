#!/bin/bash -e

LANGS="-l en -l el -l pl"

for d in zeus helios heliosauth server_ui account_administration; do
  echo $d
  (
    cd $d;
    django-admin makemessages --no-location $LANGS || true;
  )
done;

python manage.py makeboothmessages --no-location $LANGS;
