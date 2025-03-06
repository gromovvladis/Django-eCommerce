from django import template

from oscar.core.loading import get_model

register = template.Library()

Action = get_model("action", "Action")


@register.simple_tag(name="slider_actions")
def get_actions():
    """
    Gets all actions for slider
    """
    actions = []
    actions_list = Action.objects.filter(is_active=True).order_by("-order")

    for action_item in actions_list:
        actions.append(
            {
                "primary_image": action_item.primary_image,
                "description": action_item.description,
                "meta_title": action_item.meta_title,
                "meta_description": action_item.meta_description,
                "products": action_item.all_products,
                "url": action_item.get_absolute_url,
            }
        )

    return actions
