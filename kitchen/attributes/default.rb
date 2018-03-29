#
# Cookbook:: zeus
# Attributes:: default
#
# Authors: Marcin Mateusz Hanc.
# 2018
#

default['postgresql']['version'] = '9.6'
default['postgresql']['dir'] = '/var/lib/postgresql/9.6/main'
default['postgresql']['password']['postgres'] = 'qa-password'
default['postgresql']['config']['listen_addresses'] = 'localhost'
default['postgresql']['pg_hba'] =  [{
    comment: '# Vagrant user access',
    type: 'host',
    db: 'all',
    user: 'vagrant',
    addr: '127.0.0.1/32',
    method: 'md5'
}]
# default['python']['install_python2'] = false
# default['python']['install_python3'] = true
# default['python']['install_pypy']    = false
