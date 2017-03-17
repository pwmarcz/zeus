#!/bin/bash

cd /srv/deploy
puppet apply -v zeus.pp

tail -f /var/log/dmesg
