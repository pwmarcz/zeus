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
