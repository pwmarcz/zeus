#!/bin/bash

for d in zeus helios heliosauth server_ui account_administration; do
  echo $d
  (
    cd $d;
    django-admin makemessages --no-location --all || true;
  )
done;

python manage.py makeboothmessages --no-location --all;
