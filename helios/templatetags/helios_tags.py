
from django import template
from django.utils.translation import gettext as _

register = template.Library()


def _d_to_dl(d):
    html = "<dl>"
    for key in list(d.keys()):
        html += "<dt>%s</dt>" % _(key)
        value = d[key]
        if isinstance(value, dict):
            value = _d_to_dl(value)
        if isinstance(value, list):
            value = _l_to_table(value)

        html += "<dd>%s</dd>" % str(value)

    html += "</dl>"
    return html


def _l_to_table(l):
    if not len(l):
        return "<table></table>"

    html = "<table>"

    if isinstance(l[0], dict):
        values = l
        html += "<thead><tr>"
        for key in list(l[0].keys()):
            html += "<th>%s</th>" % _(key)
        html += "</thead></tr>"
    else:
        values = [{'value': v} for v in l]

    html += "<tbody>"
    for entry in values:
        html += "<tr>"
        for v in list(entry.values()):
            if isinstance(v, dict):
                v = _d_to_dl(v)
            html += "<td>%s</td>" % v
        html += "</tr>"

    html += "</tbody></table>"
    return html


@register.filter
def as_dl(d):
    return _d_to_dl(d)


as_dl.is_safe = True


@register.filter
def as_table(l):
    return _l_to_table(l)


as_dl.is_safe = True
