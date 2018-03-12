from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.client.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='zeus-client',

    version='0.1.2',

    description='Zeus client',

    long_description=long_description,

    url='https://github.com/grnet/zeus',
    author='GRNET Zeus developers',
    author_email='dev@zeus.grnet.gr',


    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],

    py_modules=['zeus.core', 'zeus.client', 'zeus.zeus_sk'],

    install_requires=['pycrypto>=2.6', 'gmpy==1.17'],

    entry_points={
        'console_scripts': [
            'zeus-client=zeus.client:main',
            'zeus-core=zeus.core:main',
        ],
    },
)
