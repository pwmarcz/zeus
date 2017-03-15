FROM debian:jessie
MAINTAINER Kostas Papadimitriou "kpap@grnet.gr"

RUN apt-get -y update
RUN apt-get -y install vim git lsb-release wget
RUN wget https://apt.puppetlabs.com/puppetlabs-release-pc1-jessie.deb
RUN apt-get -y install puppet puppet-module-puppetlabs-apt puppet-module-puppetlabs-stdlib

RUN mkdir -p /srv/data/
RUN mkdir -p /srv/static/

# cache site rules for fast docker builds
COPY deploy/grnet-zeus /etc/puppet/modules/zeus
RUN puppet module install puppetlabs-apache 
RUN puppet module install puppetlabs-postgresql
RUN puppet module install "stankevich/python"

ADD deploy/zeus-pre.pp /srv/deploy/zeus-pre.pp
ADD deploy/zeus.pp /srv/deploy/zeus.pp
ADD deploy/hiera.yaml /etc/puppet/hiera.yaml
ADD deploy/config.yaml /etc/puppet/hieraconf/common.yaml

RUN mkdir /srv/media

RUN cd /srv/deploy && puppet apply -v zeus-pre.pp

ADD deploy/boot.sh /srv/deploy/boot.sh
RUN chmod +x /srv/deploy/boot.sh

VOLUME /srv/data
VOLUME /srv/static

EXPOSE 80

CMD ["/bin/bash", "/srv/deploy/boot.sh"]
