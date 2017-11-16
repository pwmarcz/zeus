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
    $appdir = '/srv/zeus_app',
    $debug = false,
    $host = $fqdn,
    $port = 443,
    $gunicornport = 8080,
    $certdir = '/etc/ssl/',
    $admin_email = 'root@localhost',
    $institution = 'ZEUS',
    $adminuser = 'admin',
    $adminpassword = 'z3ususer',
    $secretkey = '+-evh_tc@0c03a!9w!1axzd+l#tgplunw##x1#7l7m44g3-n&5',
    $emailtls = false,
    $emailhost = 'localhost',
    $emailhostuser = false,
    $emailhostpass = false,
    $debugemail = true
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
        'ttf-dejavu-extra',
        'gettext',
        'openssl'
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
        owner => 'www-data',
        group => 'celery',
        notify  => Service['gunicorn'],
        require => [Postgresql::Server::Db[$dbname], Package['celeryd']]
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
        recurse => true,
        require => Package['celeryd']
    }

    file { '/srv/zeus-data':
        ensure => 'directory',
        owner => 'www-data',
        group => 'celery',
        mode => 0660,
        recurse => true,
        require => Package['celeryd']
    }

    file { ['/srv/zeus-data/media/', '/srv/zeus-data/media/zeus_mixes']:
        ensure => 'directory',
        owner => 'www-data',
        group => 'celery',
        mode => 0660,
        recurse => true,
        require => Package['celeryd']
    }

    file { '/etc/apache2/sites-available/20-zeus.conf':
        content => template('zeus/apache.vhost.erb'),
        notify  => Service['httpd']
    }

    file { '/etc/apache2/sites-available/zeus-common.conf':
        content => template('zeus/apache.vhost.common.erb'),
        notify  => Service['httpd']
    }

    file { '/etc/apache2/sites-enabled/20-zeus.conf':
        ensure => 'link',
        target => '/etc/apache2/sites-available/20-zeus.conf',
        notify  => Service['gunicorn']
    }

    exec {'zeus_self_signed_sslcert':
        command => "openssl req -newkey rsa:2048 -nodes -keyout private/zeus.key -x509 -days 365 -out zeus.crt -subj '/CN=${host}'",
        cwd     => $certdir,
        creates => [ "${certdir}/private/zeus.key", "${certdir}/zeus.crt", ],
        path    => ["/usr/bin", "/usr/sbin"]
    }

    exec {'zeus_migrations':
        command => "python manage.py migrate",
        cwd     => $appdir,
        path    => ["/usr/bin", "/usr/sbin"],
        require => File['zeus_settings']
    }

    exec {'zeus_compile_translations':
        command => "bash compile-translations.sh",
        cwd     => $appdir,
        path    => ["/bin", "/usr/bin", "/usr/sbin"],
        require => File['zeus_settings']
    }

    exec {'zeus_collectstatic':
        command => "python manage.py collectstatic --noinput",
        cwd     => $appdir,
        path    => ["/usr/bin", "/usr/sbin"],
        require => [File['zeus_settings'], File['/srv/zeus-data/zeus.log']],
        notify  => File['zeus_static']
    }

    file {'zeus_static': 
        name => '/srv/zeus-data/static',
        owner => 'www-data',
        group => 'celery',
        recurse => true,
        require => Exec['zeus_collectstatic']
    }

    file { 'zeus_gunicorn_log':
        path => "/srv/zeus-data/gunicorn.log",
        owner => 'www-data',
        group => 'celery',
        require => Service['gunicorn']
    }

    $logdirs = [
        '/srv/zeus-data/election_logs',
        '/srv/zeus-data/proofs',
        '/srv/zeus-data/results',
    ]
    file { $logdirs:
        ensure => 'directory',
        owner => 'www-data',
        group => 'celery',
        mode => 0660,
        require => Package['celeryd']
    }

    file { 'zeus_zeus_log':
        path => "/srv/zeus-data/zeus.log",
        owner => 'www-data',
        group => 'celery',
        require => [Service['gunicorn'], Package['celeryd'], Exec['init_user']]
    }

    file { 'celeryd_defaults': 
        path => "/etc/default/python-celery",
        content => template('zeus/celeryd.defaults.erb'),
        require => Package['celeryd']
    }

    file { 'celeryd_init': 
        path => "/etc/init.d/python-celery",
        content => template('zeus/celeryd.init.erb'),
        require => Package['celeryd'],
        mode => 0755
    }

    service { "zeus_celery":
      ensure => 'running',
      start => "/etc/init.d/python-celery start",
      stop => "/etc/init.d/python-celery stop",
      pattern => "/srv/zeus_app/manage.py celery worker",
      require => [File['celeryd_init'], File['celeryd_defaults'], File['/srv/zeus-data/zeus.log']]
    }

    exec {'init_user':
        command => "python deploy/init.py ${institution} ${adminuser} ${adminpassword}",
        cwd => $appdir,
        path => ["/usr/bin", "/usr/sbin"],
        require => [File['zeus_settings'], Exec['zeus_migrations']]
    }

    apache::listen { $port: }
}
