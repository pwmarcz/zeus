#!/bin/bash

for d in zeus helios heliosauth server_ui account_administration; do
  echo $d
  (
    cd $d;
    django-admin makemessages --no-location -l en -l el -l pl -e .html -e .txt || true;
  )
done;

python manage.py makeboothmessages --no-location -l en -l el -l pl -e .html -e .js;
