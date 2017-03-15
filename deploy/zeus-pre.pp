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
postgresql::server::db { $dbname:
  user     => hiera('dbusername'),
  password => postgresql_password(hiera('dbusername'), hiera('dbpassword')),
}

class { 'zeus': 
    dbusername => hiera('dbusername'),
    dbpassword => hiera('dbpassword'),
    dbname => hiera('dbname'),
}
