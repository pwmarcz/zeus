#!/bin/bash
docker build -t grnet/zeus-legacy .
docker volume create --name zeus-legacy-data
docker rm -f zeus-legacy
docker run \
    -P -v `pwd`/deploy/grnet-zeus:/etc/puppet/modules/zeus \
    -v `pwd`/deploy:/srv/deploy \
    -v `pwd`/:/srv/zeus_app \
    -v `pwd`/deploy/config.yaml:/etc/puppet/hieraconf/common.yaml \
    -v zeus-legacy-data:/srv/data \
    --name zeus-legacy -d grnet/zeus-legacy
