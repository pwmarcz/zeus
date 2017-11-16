#!/bin/bash
docker build -t grnet/zeus .
docker rm -f zeus
docker run \
    -P -v `pwd`/deploy/grnet-zeus:/etc/puppet/modules/zeus \
    -v `pwd`/deploy/config.yaml:/etc/puppet/hieraconf/common.yaml \
    -p 8000:8000 \
    --name zeus -d grnet/zeus
