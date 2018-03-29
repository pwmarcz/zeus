#
# Cookbook:: zeus
# Recipe:: locale
#
# Authors: Marcin Mateusz Hanc.
# 2018
#

# Currently tested only on Ubuntu 18.04 .
execute 'set locale' do
  command 'sudo update-locale LANG=en_GB.UTF-8 LC_ALL=en_GB.UTF-8'
end
