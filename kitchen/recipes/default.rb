#
# Cookbook:: zeus
# Recipe:: default
#
# Authors: Marcin Mateusz Hanc.
# 2018
#

execute 'Create postgresql user and db' do
  command 'sudo -u postgres createuser -s $(whoami)'
  # not_if 'psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname=\'$(whoami)\'"'
end
execute 'Create postgresql db' do
  command 'createdb helios -O $(whoami)'
  not_if 'psql -lqt | cut -d \| -f 1 | grep -qw helios'
end

package 'Install build-essential' do
  package_name 'build-essential'
end

package 'Install rsync' do
  package_name 'rsync'
end

package 'Install gmp' do
  package_name 'libgmp3-dev'
end

package 'Install icu' do
  package_name 'libicu-dev'
end

execute 'Copy zeus dir to home' do
  # command 'rsync -av --progress /vagrant /home/vagrant --exclude .git kitchen'
  command 'rsync -av --progress /zeus /home/vagrant --exclude .git --exclude kitchen'
  not_if {::File.exists?('/home/vagrant/zeus')}
end

python_runtime '2'

execute 'Change perms for gnu local' do
  command 'sudo chown -R vagrant:vagrant ~/.gnupg'
end

execute 'Install pipenv' do
  command 'cd zeus; pip install pipenv'
end

execute 'Generate new venv' do
  command 'cd zeus; pipenv --python python2'
end

execute 'Install dependencies' do
  command 'cd zeus; pipenv sync --dev'
end

# execute 'Create settings file' do
#   command 'cd zeus; cp settings/local_template.py settings/local.py'
#   not_if {::File.exists?('/home/vagrant/zeus/settings/local.py')}
# end
