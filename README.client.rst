Zeus client
===========

Zeus client is a command line tool to facilitate execution of advanced zeus_
election administrative operations such as cryptographical mix and partial 
decryption of submitted ballots.

.. _zeus: https://zeus.grnet.gr/


Install
-------

.. notice::

    Python 2.7 along with the pip packaging tool is required to be installed_

Installing `zeus-client` tool should be as simple as ::

    $ pip install zeus-client
    $ zeus-client --help

.. _installed: https://www.python.org/downloads/


Remote mix
----------

The `mix` command can be used for elections with `remote mixing` enabled during
initial election parametrization. Once election voting closes and zeus
completes the first mix of encrypted ballots, Zeus produces the election remote
mix URL to the election administrator. The URL can be shared across the
preferred set of participants as required by the election process. Each
participant takes part to the election mix as follows::

    - Download previously set of mixed ciphers
    - Generate a new mix
    - Upload the new ballot mix (will be used as input for the next mix)

`zeus-client` automatically takes care of all of the above steps::

    $ zeus-client mix <election-mix-url> <mix-id> <rounds> <parallel>

    # e.g.
    $ zeus-client mix https://zeus-testing.grnet.gr/zeus/elections/election-uuid/mix/unique-id my-election 128 4


- **election-mix-url** the election mix URL as provided by the election
  administrator.
- **mix-id** is an election identification string used as a prefix
  for the generated filenames.
- **rounds** is an integer related to mixnet security
  parameters. Using a low number produces fast results but could diminish mix
  security. It is advised to use an integer equal or greater than `128`.
- **parallel** should be set to the number of CPU cores of your system.
