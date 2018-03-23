# Zeus Selenium Tests

## Setting up

We'll be using Firefox. First, install it. Also download the appropriate
version of [Geckodriver](https://github.com/mozilla/geckodriver/releases) and
put it in your `PATH`.

Install Python virtualenv:

    pipenv sync
    pipenv shell

Copy `config_example.json` to `config.json`. You can customize it, or keep the
defaults so that the tests will be run against Django's testserver.

## Running

    pytest -v --driver Firefox

## Writing tests

There are two layers:

- Page objects: `LoginPage`, `CreateTestPage` etc. These should contain all the
  actual Selenium logic related to element manipulation.

- Tests. These should just use the page objects.
