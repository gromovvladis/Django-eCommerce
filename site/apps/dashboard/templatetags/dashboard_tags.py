import re
from urllib.parse import urlencode
from datetime import datetime, timedelta, date

from django.utils.timezone import now
from django import template
from core.utils import format_timedelta


from core.loading import get_class

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
def time_delta(td):
    """
    Return formatted timedelta value
    """
    return format_timedelta(td)


@register.filter
def before_order_badge(order):
    if not isinstance(order.before_order, timedelta):
        return "", "badge-danger", 0  # Если нет данных, возвращаем пустой результат

    # Рассчитываем разницу в секундах один раз
    total_seconds = int(order.before_order.total_seconds())
    in_future = total_seconds > 0
    delta = order.before_order if in_future else -order.before_order

    # Определяем цвет бейджа
    if in_future:
        before_badge = "badge-success"
    elif 0 < total_seconds < 300:  # Для времени менее 5 минут
        before_badge = "badge-warning"
    else:
        before_badge = "badge-danger"

    # Формируем текст бейджа
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60

    if days:
        before_order = f"{days} дн. {hours} ч."
    elif hours:
        before_order = f"{hours} ч. {minutes} мин."
    else:
        before_order = f"{minutes} мин."

    return before_order, before_badge, total_seconds


@register.simple_tag
def dashboard_navigation(user, request):
    return get_nodes(user, request)


@register.simple_tag
def payment_order(description):
    return int(re.findall(r"\d+", description)[0])


@register.simple_tag
def payment_date(iso_date):
    dt = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    formatted_date = dt.strftime("%d %B %Y г. %H:%M")
    formatted_date = (
        formatted_date.replace("January", "января")
        .replace("February", "февраля")
        .replace("March", "марта")
        .replace("April", "апреля")
        .replace("May", "мая")
        .replace("June", "июня")
        .replace("July", "июля")
        .replace("August", "августа")
        .replace("September", "сентября")
        .replace("October", "октября")
        .replace("November", "ноября")
        .replace("December", "декабря")
    )

    return formatted_date


@register.filter
def age(birth_date):
    """Вычисляет количество полных лет на текущую дату."""
    if not birth_date:
        return "-"

    today = date.today()
    age = today.year - birth_date.year

    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age


@register.filter
def from_now(value):
    delta = now() - value

    days = delta.days
    if days:
        return f"{days} дн."

    hours = int(delta.total_seconds() // 3600 % 24)
    if hours:
        return f"{hours} ч."

    minutes = int(delta.total_seconds() // 60 % 60)
    if minutes:
        return f"{minutes} мин."

    return "-"


@register.simple_tag
def filter_table(request, filtres):
    res = []
    for fltr in filtres["values"]:
        params = request.GET.copy()
        params.pop("status", None)
        params = urlencode(params)

        url = f'{filtres["url"]}'
        if params or fltr[0]:
            url += "?" + "&".join(filter(None, [params, fltr[0]]))

        res.append({"url": url, "name": fltr[1]})

    return res


@register.simple_tag
def delete_filter(request, params):
    query_params = request.GET.copy()

    for param in params:
        param_name, param_value = param
        if query_params.getlist(param_name) and str(param_value):
            del query_params[param_name]

    return f"{request.path}?{query_params.urlencode()}"
