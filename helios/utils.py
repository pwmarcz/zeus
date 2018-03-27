"""
Utilities.

Ben Adida - ben@adida.net
2005-04-11
"""

from __future__ import absolute_import
import random


def force_utf8(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    else:
        return s


random.seed()

def random_string(length=20):
    random.seed()
    ALPHABET = 'abcdefghkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    r_string = ''
    for i in range(length):
        r_string += random.choice(ALPHABET)

    return r_string


##
## raw SQL and locking
##

def one_val_raw_sql(raw_sql, values=[]):
    """
    for a simple aggregate
    """
    from django.db import connection
    cursor = connection.cursor()

    cursor.execute(raw_sql, values)
    return cursor.fetchone()[0]

def lock_row(model, pk):
    """
    you almost certainly want to use lock_row inside a commit_on_success function
    Eventually, in Django 1.2, this should move to the .for_update() support
    """

    from django.db import connection, transaction
    cursor = connection.cursor()

    cursor.execute("select * from " + model._meta.db_table + " where id = %s for update", [pk])
    row = cursor.fetchone()

    # if this is under transaction management control, mark the transaction dirty
    try:
        transaction.set_dirty()
    except:
        pass

    return row
