#
# Cookbook:: zeus
# Recipe:: default
#
# Authors: Marcin Mateusz Hanc.
# 2018
#

execute 'Create postgresql user and db' do
  command 'sudo -u postgres createuser -s vagrant'
  # not_if 'psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname=\'vagrant\'"'
end
execute 'Create postgresql db' do
  command "su vagrant -l -c 'createdb helios -O vagrant'"
  # not_if 'psql -lqt | cut -d \| -f 1 | grep -qw helios'
end

package 'Install build-essential' do
  package_name 'build-essential'
end

package 'Install rsync' do
  package_name 'rsync'
end

package 'Install icu' do
  package_name 'libicu-dev'
end

package 'Install gmp' do
  package_name 'libgmp-dev'
end

package 'Install mpfr' do
  package_name 'libmpfr-dev'
end

package 'Install mpc' do
  package_name 'libmpc-dev'
end


python_runtime '3.6' do
  provider :system
  version '3.6'
  options :system, package_name: 'python3'
end

execute 'Change perms for gnu local' do
  command 'sudo chown -R vagrant:vagrant ~/.gnupg'
end

execute 'Copy zeus dir to home' do
  command 'rsync -av --progress /zeus /home/vagrant --exclude .git --exclude kitchen'
  not_if {::File.exists?('/home/vagrant/zeus')}
end

execute 'Install pipenv' do
  command "cd zeus; sudo pip install pipenv"
  action :run
end

execute 'Generate new venv' do
  command "su vagrant -l -c 'cd zeus; pipenv --python python3.6'"
  action :run
end

execute 'Install dependencies' do
  command "su vagrant -l -c 'cd zeus; pipenv sync --dev'"
  action :run
end

# execute 'Create settings file' do
#   command 'cd zeus; cp settings/local_template.py settings/local.py'
#   not_if {::File.exists?('/home/vagrant/zeus/settings/local.py')}
# end
