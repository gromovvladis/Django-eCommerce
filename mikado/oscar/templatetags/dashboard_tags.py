import re
from django import template
from datetime import datetime, timedelta
from oscar.core.loading import get_class
from urllib.parse import urlencode

get_nodes = get_class("dashboard.menu", "get_nodes")
register = template.Library()

@register.filter
def tab(text, paths):
    for path in paths:
        if text.startswith(path):
            return True
    return False

@register.filter
def subtab(text, path):
    if text.startswith(path):
        return True
    return False

@register.filter
def in_future(value):
    if isinstance(value, timedelta):
        return value > timedelta(0)
    return False

@register.filter
def hours(value):
    if isinstance(value, timedelta):
        return int(value.total_seconds() // 3600 % 24)
    return 0

@register.filter
def minutes(value):
    if isinstance(value, timedelta):
        minutes = int(value.total_seconds() // 60 % 60) 
        return minutes if minutes < 61 else 0
    return 0

@register.simple_tag
def dashboard_navigation(user):
    return get_nodes(user)

@register.simple_tag
def payment_order(description):
    return int(re.findall(r'\d+', description)[0])

@register.simple_tag
def payment_date(iso_date):
    dt = datetime.strptime(iso_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    formatted_date = dt.strftime('%d %B %Y г. %H:%M')
    formatted_date = formatted_date.replace('January', 'января') \
                                .replace('February', 'февраля') \
                                .replace('March', 'марта') \
                                .replace('April', 'апреля') \
                                .replace('May', 'мая') \
                                .replace('June', 'июня') \
                                .replace('July', 'июля') \
                                .replace('August', 'августа') \
                                .replace('September', 'сентября') \
                                .replace('October', 'октября') \
                                .replace('November', 'ноября') \
                                .replace('December', 'декабря')

    return formatted_date

@register.simple_tag
def filter_table(request, filtres):
    res = []
    for fltr in filtres["values"]:
        params = request.GET.copy()
        params.pop('status', None)
        params = urlencode(params)

        url = f'{filtres["url"]}'
        if params or fltr[0]:
            url += '?' + '&'.join(filter(None, [params, fltr[0]]))

        res.append({
            "url": url,
            "name": fltr[1]
        })
        
    return res