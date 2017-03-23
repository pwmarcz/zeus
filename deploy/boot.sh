#!/bin/bash

cd /srv/deploy
puppet apply -v zeus.pp

tail -f /srv/zeus-data/*log /srv/zeus-data/election_logs/*
