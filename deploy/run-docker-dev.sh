#!/bin/bash
docker build -t grnet/zeus .
docker rm -f zeus-dev
docker run \
    -P -v `pwd`/deploy/grnet-zeus:/etc/puppet/modules/zeus \
    -v `pwd`/deploy:/srv/deploy \
    -v `pwd`/:/srv/zeus_app \
    -v `pwd`/deploy/config.yaml:/etc/puppet/hieraconf/common.yaml \
    -p 8001:8001 \
    --name zeus-dev -d grnet/zeus
