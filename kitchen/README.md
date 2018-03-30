# kitchen

Simple cookbook for running the zeus project inside the virtualbox VM through with vagrant.

To use it you need virtualbox, vagrant and chefdk.

## How to use it

    kitchen create
    kitchen converge
    kitchen login

Then follow it up with instructions from zeus README:

    cd zeus
    pipenv shell

    cp settings/local_template.py settings/local.py

    python manage.py migrate

    python manage.py manage_users --create-institution "ZEUS"
    python manage.py manage_users --create-user <username> --institution=1

To test system:

    pytest -v

## How to run system locally

Add to your `settings/local.py` file:

    ALLOWED_HOSTS = ['*']

And run the server:

    python manage.py runserver 10.0.42.42:8000
