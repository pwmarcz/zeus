class { 'apache': 
    default_mods => ['autoindex', 'mime', 'deflate', 'setenvif', 'dir', 'env', 'reqtimeout', 'proxy', 'proxy_http', 'rewrite', 'xsendfile', 'headers']
}
class { 'apache::mod::ssl': }

class { 'postgresql::globals':
  needs_initdb => true,
  encoding => 'UTF-8'
}->
class { 'postgresql::server': }

$dbname = hiera('zeus::dbname')
$dbusername = hiera('zeus::dbusername')
$dbpassword = hiera('zeus::dbpassword')

postgresql::server::role { $dbusername:
  password_hash => postgresql_password($dbusername, $dbpassword),
  createdb => true
}

postgresql::server::db { $dbname:
  owner => $dbusername,
  user => $dbusername,
  password => postgresql_password($dbusername, $dbpassword),
}

postgresql::server::db { "test_${dbname}":
  owner => $dbusername,
  user => $dbusername,
  password => postgresql_password($dbusername, $dbpassword)
}

service { "gunicorn":
    ensure  => "running",
    enable  => "true",
}

class { 'zeus': }
