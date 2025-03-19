from django import http
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, View
from core.loading import get_model, get_classes

PageTitleMixin, ThemeMixin = get_classes(
    "webshop.mixins", ["PageTitleMixin", "ThemeMixin"]
)


WishList = get_model("wishlists", "WishList")
Line = get_model("wishlists", "Line")
Product = get_model("catalogue", "Product")


class WishListDetailView(PageTitleMixin, ThemeMixin, ListView):
    """
    This view acts as a DetailView for a wish list and allows updating the
    quantities of products.

    It is implemented as FormView because it's easier to adapt a FormView to
    display a product then adapt a DetailView to handle form validation.
    """

    template_name = "webshop/customer/wishlists/wishlists_detail.html"
    context_object_name = "products"
    active_tab = "wishlist"
    page_title = "Избранное"
    paginate_by = settings.PRODUCTS_PER_PAGE

    def get_queryset(self):
        return self.object.lines.all()

    def dispatch(self, request, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self.object = self.get_wishlist_or_404(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_wishlist_or_404(self, user):
        wishlist, created = WishList.objects.get_or_create(owner_id=user.id)
        if wishlist.is_allowed_to_edit(user):
            return wishlist
        else:
            raise Http404

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["wishlist"] = self.object
        ctx["content_open"] = True
        ctx["summary"] = "profile"
        return ctx


class WishListAddProduct(View):
    """
    Adds a product to a wish list.

    - If the user doesn't already have a wishlist then it will be created for
      them.
    - If the product is already in the wish list, its quantity is increased.
    """

    # pylint: disable=attribute-defined-outside-init
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs["product_pk"])
        self.wishlist = self.get_or_create_wishlist(request, *args, **kwargs)
        return super().dispatch(request)

    def get_or_create_wishlist(self, request, *args, **kwargs):
        if "key" in kwargs:
            wishlist = get_object_or_404(
                WishList, key=kwargs["key"], owner=request.user
            )
        else:
            wishlist = request.user.wishlist
            if not wishlist:
                return request.user.wishlist.create()

        if not wishlist.is_allowed_to_edit(request.user):
            raise PermissionDenied
        return wishlist

    def post(self, request, *args, **kwargs):
        return self.add_product()

    def add_product(self):
        self.wishlist.add(self.product)
        return http.JsonResponse(
            {
                "html": '<svg width="24" height="24"><use xlink:href="#add-to-wishlist"></use></svg>',
                "url": reverse_lazy(
                    "customer:wishlist-remove-product",
                    kwargs={"product_pk": self.product.id},
                ),
                "status": 200,
            },
            status=200,
        )


class LineMixin(object):
    """
    Handles fetching both a wish list and a product
    Views using this mixin must be passed two keyword arguments:

    * key: The key of a wish list
    * line_pk: The primary key of the wish list line

    or

    * product_pk: The primary key of the product
    """

    def fetch_line(self, user, product_pk):
        try:
            wishlist = WishList.objects.get(owner_id=user.id)
            self.line = get_object_or_404(
                Line,
                product_id=product_pk,
                wishlist__owner=user,
                wishlist__key=wishlist.key,
            )
        except Line.MultipleObjectsReturned:
            raise Http404
        self.wishlist = self.line.wishlist
        self.product = self.line.product


class WishListRemoveProduct(LineMixin, View):
    def get_object(self, queryset=None):
        self.fetch_line(
            self.request.user,
            self.kwargs.get("product_pk"),
        )
        return self.line

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self._delete()

    def _delete(self):
        self.object.delete()
        return http.JsonResponse(
            {
                "html": '<svg width="24" height="24"><use xlink:href="#remove-from-wishlist"></use></svg>',
                "url": reverse_lazy(
                    "customer:wishlist-add-product",
                    kwargs={"product_pk": self.product.id},
                ),
                "status": 200,
            },
            status=200,
        )

    def get_success_response(self):
        return redirect(reverse("customer:wishlist"))
