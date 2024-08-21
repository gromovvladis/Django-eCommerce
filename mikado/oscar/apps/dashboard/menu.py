from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from django.utils import timezone

from oscar.core.loading import get_class, get_model

Node = get_class("dashboard.nav", "Node")

StockAlert = get_model("partner", "StockAlert")
Order = get_model("order", "Order")
ProductReview = get_model("reviews", "ProductReview")
OrderReview = get_model("customer", "OrderReview")
DeliveryOrder = get_model("delivery", "DeliveryOrder")


def get_nodes(user):
    """
    Return the visible navigation nodes for the passed user
    """
    all_nodes = create_menu(settings.OSCAR_DASHBOARD_NAVIGATION)
    visible_nodes = []
    for node in all_nodes:
        filtered_node = node.filter(user)
        # don't append headings without children
        if filtered_node and (
            filtered_node.has_children() or not filtered_node.is_heading
        ):
            visible_nodes.append(filtered_node)
    return visible_nodes


def create_menu(menu_items, parent=None):
    """
    Create the navigation nodes based on a passed list of dicts
    """
    nodes = []
    models = {
        "orders": Order.objects.filter(date_finish__isnull=True),
        "delivery": DeliveryOrder.objects.filter(pickup_time__gt=timezone.now())
    }
    default_fn = import_string(settings.OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION)
    for menu_dict in menu_items:
        try:
            label = menu_dict["label"]
        except KeyError:
            raise ImproperlyConfigured("No label specified for menu item in dashboard")

        children = menu_dict.get("children", [])
        if children:
            node = Node(
                label=label,
                icon=menu_dict.get("icon", None),
                notif=get_parent_notif(children, models),
                access_fn=menu_dict.get("access_fn", default_fn),
            )
            create_menu(children, parent=node)
        else:
            node = Node(
                label=label,
                icon=menu_dict.get("icon", None),
                notif=get_notif(menu_dict.get("notification", None), models),
                url_name=menu_dict.get("url_name", None),
                url_kwargs=menu_dict.get("url_kwargs", None),
                url_args=menu_dict.get("url_args", None),
                access_fn=menu_dict.get("access_fn", default_fn),
            )
        if parent is None:
            nodes.append(node)
        else:
            parent.add_path(node.url)
            parent.add_child(node)
    return nodes


def get_parent_notif(children, models):
    total_notif = 0
    for child in children:
        if "children" in child and child["children"]:
            # Если у дочернего элемента есть свои дочерние, суммируем их notif рекурсивно
            total_notif += get_parent_notif(child["children"])
        else:
            # Если это листовой элемент, добавляем его notif
            notif = get_notif(child.get("notification", None), models, child.get("notif_count", None))
            child["notif_count"] = notif
            total_notif += notif
    return total_notif


def get_notif(notif, models, count=None):

    orders = models['orders']
    delivery = models['delivery']

    if count:
        return count
    if notif:
        function_map = {
            'stock_alerts': stock_alerts,
            'active_orders': active_orders(orders),
            'all_orders': all_orders(orders),
            'feedback_product': feedback_product,
            'feedback_order': feedback_order,
            'delivery_now': delivery_now(delivery),
            'delivery_kitchen': delivery_kitchen(delivery),
            'delivery_couriers': delivery_couriers(delivery),
        }
        function_to_call = function_map.get(notif)
        if function_to_call:
            return function_to_call()
        else:
            return 0
    return 0

def stock_alerts():
    return StockAlert.objects.filter(status=StockAlert.OPEN).count()

def active_orders(orders):
    active_statuses = ['Ожидает оплаты', 'Оплачен', 'Обрабатывается', 'Готовится', 'Готов', 'Доставляется']
    return orders.filter(is_open=False, status__in=active_statuses).count()

def all_orders(orders):
    return orders.filter(is_open=False).count()

def feedback_product():
    return ProductReview.objects.filter(is_open=False).count()

def feedback_order():
    return OrderReview.objects.filter(is_open=False).count()

def delivery_now(delivery):
    return delivery.all().count()

def delivery_kitchen(delivery):
    return delivery.all().count()

def delivery_couriers(delivery):
    return delivery.all().count()
