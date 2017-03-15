$dbusername = hiera('dbusername')
$dbpassword = hiera('dbpassword')
$dbname = hiera('dbname')

class { 'postgresql::server': }->
postgresql::server::db { $dbname:
  user => $dbusername,
  password => postgresql_password($dbusername, $dbpassword)
}
