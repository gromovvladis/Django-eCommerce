import xml.etree.ElementTree as ET

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ICON_DIR = "mikado/mikado/static/svg"

@register.simple_tag
def icon(file_name, class_str=None, size=None, fill=None, stroke=None):
    """Inlines a SVG icon from linkcube/src/core/assets/templates/core.assets/icon

    Example usage:
        {% icon 'face' 'std-icon menu-icon' 32 '#ff0000' %}
    Parameter: file_name
        Name of the icon file excluded the .svg extention.
    Parameter: class_str
        Adds these class names, use "foo bar" to add multiple class names.
    Parameter: size
        An integer value that is applied in pixels as the width and height to
        the root element.
        The material.io icons are by default 24px x 24px.
    Parameter: fill
        Sets the fill color of the root element.
    Returns:
        XML to be inlined, i.e.:
        <svg width="..." height="..." fill="...">...</svg>
    """
    path = f'{ICON_DIR}/{file_name}.svg'
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(path)
    root = tree.getroot()
    if class_str:
        root.set('class', class_str)
    if stroke:
        root.set('stroke', stroke)
    if size:
        root.set('height', f'{size}px')
    if fill:
        root.set('fill', fill)
    svg = ET.tostring(root, encoding="unicode", method="html")
    return mark_safe(svg)