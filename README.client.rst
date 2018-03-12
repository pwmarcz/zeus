Zeus client
===========

Zeus client is a command line tool for to facilitate execution of advanced
zeus_ election administrative operations such as cryptographical mixing and
partial decryption.

.. _zeus: https://zeus.grnet.gr/


Install
-------

.. notice::

    Python along with pip packaging tool is required to be installed_

Installing client should be as simple as ::

    $ pip install zeus-client

.. _installed: https://www.python.org/downloads/


Remote mix
----------

`mix` command can be used for elections with `remote mixing` enabled during initial
election parametrization. Once election voting closes and zeus completes the first 
mix of encrypted ballots, election admin is provided the election remote mix URL. 
This URL can be shared across the preferred set of participants, as required by 
the election process. Each mix-network participant takes part to the election mix 
as follows::

    - Download previously set of mixed ciphers
    - Generate a new mix
    - Upload the mix for the next participant to continue

`zeus-client` takes care of the above using the following command::

    $ zeus-client mix <election-mix-url> <mix-id> <rounds> <parallel>

    # e.g.
    $ zeus-client mix https://zeus-testing.grnet.gr/zeus/elections/election-uuid/mix/unique-id my-election 128 4


`mix-id` is an election identification string used as a prefix for the generated 
filenames.
`rounds` is an integer related to mixnet security parameters. Using a low number produces fast results 
but could diminish mix security. It is advised to use an integer equal or greater to `128`.
`parallel` should be set to the number of CPU cores of your system.
