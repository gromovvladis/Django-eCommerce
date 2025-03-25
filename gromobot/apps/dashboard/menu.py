from core.loading import get_class, get_model
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.utils.module_loading import import_string

Node = get_class("dashboard.nav", "Node")

StockAlert = get_model("store", "StockAlert")
Order = get_model("order", "Order")
OrderReview = get_model("order_reviews", "OrderReview")
ProductReview = get_model("product_reviews", "ProductReview")
ShippingOrder = get_model("shipping", "ShippingOrder")


def get_nodes(user, request):
    """
    Return the visible navigation nodes for the passed user
    """
    models = {
        "stock_alerts": StockAlert.objects.filter(
            status=StockAlert.OPEN, stockrecord__store__in=request.staff_stores
        ),
        "orders": request.no_finish_orders,
        "active_orders": request.active_orders,
        "shipping": ShippingOrder.objects.filter(
            pickup_time__gt=timezone.now(), store__in=request.staff_stores
        ),
        "product_reviews": ProductReview.objects.filter(
            is_open=False,
        ),
        "order_reviews": OrderReview.objects.filter(is_open=False),
    }
    all_nodes = create_menu(settings.DASHBOARD_NAVIGATION, models)
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
    default_fn = import_string(settings.DASHBOARD_DEFAULT_ACCESS_FUNCTION)
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
            "shipping_active": shipping_active,
            "shipping_store": shipping_store,
            "shipping_couriers": shipping_couriers,
        }
        function_to_call = function_map.get(child["notification"])
        if function_to_call:
            return function_to_call(models)

    return 0


def stock_alerts(models):
    return models["stock_alerts"].count()


def active_orders(models):
    return models["active_orders"]


def all_orders(models):
    return models["orders"].filter(is_open=False).count()


def feedback_product(models):
    return models["product_reviews"].count()


def feedback_order(models):
    return models["order_reviews"].count()


def shipping_active(models):
    return models["shipping"].count()


def shipping_store(models):
    return models["shipping"].count()


def shipping_couriers(models):
    return models["shipping"].count()
