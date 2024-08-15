import re
from django import template
from datetime import datetime
from oscar.core.loading import get_class

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
