#!/bin/bash -e

unset DJANGO_SETTINGS_MODULE

for d in zeus helios heliosauth server_ui account_administration; do
    (
        echo $d
        cd $d
        django-admin compilemessages
    )
done

cd zeus/static/booth
django-admin compilemessages
