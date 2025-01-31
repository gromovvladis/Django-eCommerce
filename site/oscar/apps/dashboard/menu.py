from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from django.utils import timezone

from oscar.core.loading import get_class, get_model

Node = get_class("dashboard.nav", "Node")

StockAlert = get_model("store", "StockAlert")
Order = get_model("order", "Order")
ProductReview = get_model("reviews", "ProductReview")
OrderReview = get_model("customer", "OrderReview")
DeliveryOrder = get_model("delivery", "DeliveryOrder")


def get_nodes(user, request):
    """
    Return the visible navigation nodes for the passed user
    """
    models = {
        "stock_alert": StockAlert.objects.filter(
            status=StockAlert.OPEN, stockrecord__store__in=request.staff_stores
        ),
        "orders": request.no_finish_orders,
        "active_orders": request.active_orders,
        "delivery": DeliveryOrder.objects.filter(
            pickup_time__gt=timezone.now(), store__in=request.staff_stores
        ),
        "product_review": ProductReview.objects.filter(
            is_open=False,
        ),
        "order_review": OrderReview.objects.filter(is_open=False),
    }
    all_nodes = create_menu(settings.OSCAR_DASHBOARD_NAVIGATION, models)
    visible_nodes = []
    for node in all_nodes:
        filtered_node = node.filter(user)
        # don't append headings without children
        if filtered_node and (
            filtered_node.has_children() or not filtered_node.is_heading
        ):
            visible_nodes.append(filtered_node)
    return visible_nodes


def create_menu(menu_items, models, parent=None):
    """
    Create the navigation nodes based on a passed list of dicts
    """
    nodes = []
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
            create_menu(children, models, parent=node)
        else:
            node = Node(
                label=label,
                icon=menu_dict.get("icon", None),
                notif=get_notif(menu_dict, models),
                url_name=menu_dict.get("url_name", None),
                url_kwargs=menu_dict.get("url_kwargs", None),
                url_args=menu_dict.get("url_args", None),
                access_fn=menu_dict.get("access_fn", default_fn),
            )
        if parent is None or children:
            nodes.append(node)
        else:
            parent.add_path(node.url)
            parent.add_child(node)
    return nodes


def get_parent_notif(children, models):
    total_notif = 0
    pass_notif = ["all_orders"]
    for child in children:
        if "children" in child and child["children"]:
            # Если у дочернего элемента есть свои дочерние, суммируем их notif рекурсивно
            total_notif += get_parent_notif(child["children"], models)
        else:
            # Если это листовой элемент, добавляем его notif
            if child.get("notification") in pass_notif:
                continue
            total_notif += get_notif(child, models)

    return total_notif


def get_notif(child, models):
    if child.get("notification"):
        function_map = {
            "stock_alerts": stock_alerts,
            "active_orders": active_orders,
            "all_orders": all_orders,
            "feedback_product": feedback_product,
            "feedback_order": feedback_order,
            "delivery_active": delivery_active,
            "delivery_store": delivery_store,
            "delivery_couriers": delivery_couriers,
        }
        function_to_call = function_map.get(child["notification"])
        if function_to_call:
            return function_to_call(models)

    return 0


def stock_alerts(models):
    stock_alert = models["stock_alert"]
    return stock_alert.count()


def active_orders(models):
    return models["active_orders"]


def all_orders(models):
    orders = models["orders"]
    return orders.filter(is_open=False).count()


def feedback_product(models):
    product_review = models["product_review"]
    return product_review.count()


def feedback_order(models):
    order_review = models["order_review"]
    return order_review.count()


def delivery_active(models):
    delivery = models["delivery"]
    return delivery.count()


def delivery_store(models):
    delivery = models["delivery"]
    return delivery.count()


def delivery_couriers(models):
    delivery = models["delivery"]
    return delivery.count()
