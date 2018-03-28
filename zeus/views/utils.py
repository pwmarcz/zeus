

def set_menu(menu, ctx):
    ctx['menu_active'] = menu


def common_json_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return str(obj)
