# == Class: zeus
#
# Full description of class zeus here.
#
# === Parameters
#
# Document parameters here.
#
# [*sample_parameter*]
#   Explanation of what this parameter affects and what it defaults to.
#   e.g. "Specify one or more upstream ntp servers as an array."
#
# === Variables
#
# Here you should define a list of variables that this module would require.
#
# [*sample_variable*]
#   Explanation of how this variable affects the funtion of this class and if
#   it has a default. e.g. "The parameter enc_ntp_servers must be set by the
#   External Node Classifier as a comma separated list of hostnames." (Note,
#   global variables should be avoided in favor of class parameters as
#   of Puppet 2.6.)
#
# === Examples
#
#  class { 'zeus': }
#
# === Authors
#
# Author Name <author@domain.com>
#
# === Copyright
#
# Copyright 2017 Your name here, unless otherwise noted.
#
class zeus (
    $dbname,
    $dbpassword,
    $dbusername
) {

    $packages = [
        'python-django',
        'rabbitmq-server',
        'python-django-picklefield',
        'python-psycopg2',
        'python-celery',
        'python-django-celery',
        'python-kombu',
        'gunicorn',
        'python-pyicu',
        'python-django-pagination',
        'python-django-south',
        'python-openid',
        'python-gmpy',
        'python-simplejson',
        'python-crypto',
    ]

    package { $packages: 
        ensure => 'installed'
    }

    $test1 = "testfile var:${dbname}"
    file { '/srv/code/local_settings.py': 
        content => template('zeus/local_settings.py.erb')
    }
}
