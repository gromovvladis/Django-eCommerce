from django import template

from oscar.core.loading import feature_hidden

register = template.Library()


@register.simple_tag(takes_context=True)
def get_parameters(context, except_field):
    """
    Renders current get parameters except for the specified parameter
    """
    getvars = context["request"].GET.copy()
    getvars.pop(except_field, None)

    if len(getvars.keys()) > 0:
        return "%s&" % getvars.urlencode()

    return ""
