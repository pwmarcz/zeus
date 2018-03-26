name 'zeus'
maintainer 'Marcin Mateusz Hanc'
maintainer_email 'marcin.mateusz.hanc@gmail.com'
description 'Installs/Configures kitchen for test runs of Zeus'
long_description 'Installs/Configures kitchen for test runs of Zeus'
version '0.1.0'
chef_version '>= 12.14' if respond_to?(:chef_version)
source_url 'https://github.com/pwmarcz/zeus/kitchen'
issues_url 'https://github.com/pwmarcz/zeus/issues/labels/kitchen'

depends "postgresql"
depends 'poise-python', '~> 1.6.0'
