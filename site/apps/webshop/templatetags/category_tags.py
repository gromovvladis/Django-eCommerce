from django import template
from django.core.cache import cache
from core.loading import get_model

register = template.Library()
Category = get_model("catalogue", "category")


class PassThrough(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, objtype):
        if obj is None:
            return self

        return getattr(obj.category, self.name)


class CategoryFieldPassThroughMetaClass(type):
    """
    Add accessors for category fields to whichever class is of this type.
    """

    def __new__(cls, name, bases, attrs):
        field_accessors = {}
        for field in Category._meta.get_fields():
            name = field.name
            field_accessors[name] = PassThrough(name)

        # attrs win of silly field accessors
        field_accessors.update(attrs)
        return type.__new__(cls, name, bases, field_accessors)


class CheapCategoryInfo(dict, metaclass=CategoryFieldPassThroughMetaClass):
    """
    Wrapper class for Category.

    Besides allowing inclusion of extra info, useful while rendering a template,
    this class hides any expensive properties people should not use by accident
    in templates.

    This replaces both the node as the info object returned by the ``category_tree``
    templatetag, so it mimics a tuple of 2 items (which are the same) for
    backwards compatibility.
    """

    def __init__(self, category, **info):
        super().__init__(info)
        self.category = category

    @property
    def pk(self):
        return self.category.pk

    def get_absolute_url(self):
        return self["url"]

    def __len__(self):
        "Mimic a tuple of 2 items"
        return 2

    def __iter__(self):
        "be an iterable of 2 times the same item"
        yield self
        yield self


@register.simple_tag(name="category_tree")
def get_annotated_list(depth=None, parent=None):
    """
    Gets an annotated list from a tree branch.
    Borrows heavily from treebeard's get_annotated_list
    """
    # 'depth' is the backwards-compatible name for the template tag,
    # 'max_depth' is the better variable name.

    categories = cache.get("categories")

    if not categories:
        max_depth = depth

        annotated_categories = []
        tree_slug = ""

        start_depth, prev_depth = (None, None)
        if parent:
            categories = parent.get_descendants()
            tree_slug = parent.get_full_slug()
            if max_depth is not None:
                max_depth += parent.get_depth()
        else:
            categories = Category.get_tree()

        if max_depth is not None:
            categories = categories.filter(depth__lte=max_depth)

        categories = categories.browsable()

        info = CheapCategoryInfo(parent, url="")

        for node in categories:
            node_depth = node.get_depth()
            if start_depth is None:
                start_depth = node_depth

            # Update previous node's info
            if prev_depth is None or node_depth > prev_depth:
                info["has_children"] = True
                if info.category is not None:
                    tree_slug = info.category.get_full_slug(tree_slug)

            if prev_depth is not None and node_depth < prev_depth:
                depth_difference = prev_depth - node_depth
                info["num_to_close"] = list(range(0, depth_difference))
                tree_slugs = tree_slug.rsplit(node._slug_separator, depth_difference)
                if tree_slugs:
                    tree_slug = tree_slugs[0]
                else:
                    tree_slug = node.slug

            info = CheapCategoryInfo(
                node,
                url=node._get_absolute_url(tree_slug),
                num_to_close=[],
                level=node_depth - start_depth,
                primary_image=node.primary_image,
            )
            annotated_categories.append(info)

            prev_depth = node_depth

        if prev_depth is not None:
            # close last leaf
            info["num_to_close"] = list(range(0, prev_depth - start_depth))
            info["has_children"] = prev_depth > prev_depth

        cache.set("categories", annotated_categories, 3600)
        categories = annotated_categories

    return categories


@register.simple_tag(name="root_categories")
def get_categories_list():
    """
    Gets only root categories.
    """
    categories = cache.get("root_categories")

    if not categories:
        # Получаем корневые категории (только те, у которых глубина равна 1)
        categories = Category.objects.filter(depth=1).browsable()

        annotated_categories = []

        for node in categories:
            info = CheapCategoryInfo(
                node,
                url=node._get_absolute_url(),
                num_to_close=[],
                level=0,
                primary_image=node.primary_image,
            )
            annotated_categories.append(info)

        cache.set("root_categories", annotated_categories, 3600)
        categories = annotated_categories

    return categories


@register.simple_tag(name="subcategory_tree")
def get_child_categories(parent):
    """
    Gets only child categories of a specified parent category.
    """
    cache_key = f"child_categories_{parent.pk}"
    categories = cache.get(cache_key)

    if not categories:
        categories = parent.get_children().browsable()

        annotated_categories = []

        for node in categories:
            info = CheapCategoryInfo(
                node,
                url=node._get_absolute_url(),
                num_to_close=[],
                level=1,
                primary_image=node.primary_image,
            )
            annotated_categories.append(info)

        cache.set(cache_key, annotated_categories, 3600)
        categories = annotated_categories

    return categories
