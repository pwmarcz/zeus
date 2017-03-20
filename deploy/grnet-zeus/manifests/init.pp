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
    $dbusername,
    $appdir = '/srv/zeus_app'
) {

    $packages = [
        'python-django',
        'rabbitmq-server',
        'python-django-picklefield',
        'python-psycopg2',
        'python-celery',
        'python-django-celery',
        'celeryd',
        'python-kombu',
        'gunicorn',
        'python-pyicu',
        'python-django-pagination',
        'python-openid',
        'python-gmpy',
        'python-simplejson',
        'python-crypto',
        'python-reportlab',
        'ttf-dejavu',
        'ttf-dejavu-core',
        'ttf-dejavu-extra'
    ]

    $dev_packages = [
        'python-pytest',
        'curl', 'vim'
    ]

    package { $packages: ensure => 'installed' }
    package { $dev_packages: ensure => 'installed' }

    # south is not compatible with django1.7
    package { 'python-django-south':
        ensure => 'absent'
    }

    file { 'zeus_settings':
        path => "${appdir}/local_settings.py",
        content => template('zeus/local_settings.py.erb'),
        notify  => Service['gunicorn']
    }

    file { 'zeus_gunicorn_conf':
        path => "/etc/gunicorn.d/zeus",
        content => template('zeus/zeus.gunicorn.erb'),
        notify  => Service['gunicorn']
    }

    file { 'zeus_app_dir':
        name => $appdir,
        ensure => 'directory',
        owner => 'www-data',
        group => 'celery',
        recurse => true
    }

    file { '/srv/zeus-data':
        ensure => 'directory',
        owner => 'www-data',
        group => 'celery',
        recurse => true
    }

}
