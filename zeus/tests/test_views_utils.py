
import datetime


from zeus.views import utils


def test_set_menu():
    menu = 'menu'
    ctx = {}
    utils.set_menu(menu, ctx)
    assert ctx['menu_active'] == menu


def test_common_json_handler():
    date = datetime.datetime.strptime('2015-05-16', '%Y-%m-%d')
    assert utils.common_json_handler(date) == '2015-05-16T00:00:00'
    assert utils.common_json_handler('somestring') == 'somestring'

    class DummyObject(object):
        def __unicode__(self):
            return 'a unicode representation'

    assert utils.common_json_handler(DummyObject()) == 'a unicode representation'
