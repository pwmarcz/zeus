class { 'apache': 
    default_mods => ['autoindex', 'mime', 'deflate', 'setenvif', 'dir', 'env', 'reqtimeout']
}
class { 'apache::mod::ssl': }

class { 'postgresql::globals':
  needs_initdb => true,
  encoding => 'UTF-8',
  datadir => '/srv/data/database'
}->
class { 'postgresql::server': }

$dbname = hiera('dbname')
$dbusername = hiera('dbusername')
$dbpassword = hiera('dbpassword')

postgresql::server::db { $dbname:
  user     => $dbusername,
  password => postgresql_password($dbusername, $dbpassword),
  owner    => $dbusername
}
postgresql::server::db { "test_${dbname}":
  user     => $dbusername,
  password => postgresql_password($dbusername, $dbpassword),
  owner    => $dbusername
}

postgresql::server::role { $dbusername: 
  createdb => true
}

service { "gunicorn":
    ensure  => "running",
    enable  => "true",
}

class { 'zeus': 
    dbusername => hiera('dbusername'),
    dbpassword => hiera('dbpassword'),
    dbname => hiera('dbname'),
}
