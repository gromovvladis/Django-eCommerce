from django import http
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    UpdateView,
    View,
    DetailView,
)

# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated

from oscar.core.loading import get_class, get_classes, get_model
from oscar.core.utils import is_ajax, redirect_to_referrer, safe_referrer

WishList = get_model("wishlists", "WishList")
Line = get_model("wishlists", "Line")
Product = get_model("catalogue", "Product")
PageTitleMixin = get_class("customer.mixins", "PageTitleMixin")

# WishListForm = get_class("wishlists.forms", "WishListForm")
# LineFormset, WishListSharedEmailFormset = get_classes(
#     "wishlists.formsets", ("LineFormset", "WishListSharedEmailFormset")
# )
# LineFormset = get_class("wishlists.formsets","LineFormset")


class WishListDetailView(PageTitleMixin, ListView):
    """
    This view acts as a DetailView for a wish list and allows updating the
    quantities of products.

    It is implemented as FormView because it's easier to adapt a FormView to
    display a product then adapt a DetailView to handle form validation.
    """

    template_name = "oscar/customer/wishlists/wishlists_detail.html"
    context_object_name = "products"
    active_tab = "wishlist"
    page_title = "Избранное"
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE

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
        ctx["summary"] = "Профиль"
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
            wishlists = request.user.wishlists.all()[:1]
            if not wishlists:
                return request.user.wishlists.create()
            wishlist = wishlists[0]

        if not wishlist.is_allowed_to_edit(request.user):
            raise PermissionDenied
        return wishlist

    def post(self, request, *args, **kwargs):
        return self.add_product()

    def add_product(self):
        self.wishlist.add(self.product)
        return http.JsonResponse({
            "html": '<svg width="24" height="24"><use xlink:href="#add-to-wishlist"></use></svg>',
            "url": reverse_lazy('customer:wishlist-remove-product', kwargs={"product_pk": self.product.id})
            }, status=200)


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
        if is_ajax(self.request):
            return http.JsonResponse({
                "html": '<svg width="24" height="24"><use xlink:href="#remove-from-wishlist"></use></svg>',
                "url": reverse_lazy('customer:wishlist-add-product', kwargs={"product_pk": self.product.id})
                }, status=200)
        
        return self.get_success_response()

    def get_success_response(self):
        return redirect(reverse("customer:wishlist"))
    





# class WishListCreateUpdateViewMixin(PageTitleMixin):
#     """
#     The wishlist create and update view have the same approach on saving the wislist and shared email
#     forms. This mixin handles that in the post view, where it will call process_wishlist_forms
#     if both forms are valid. If one of the forms is not valid, the user will be redirected to the original
#     view with form errors.
#     """

#     def process_wishlist_forms(self, wishlist_form, shared_emails_formset):
#         wishlist = wishlist_form.save()

#         # for form in shared_emails_formset:
#         #     # Prevents saving empty or unchanged forms in the formset.
#         #     if not form.has_changed():
#         #         continue

#         #     # Don't commit to DB until we saved the wislist instance.
#         #     wishlist_shared_email = form.save(commit=False)
#         #     wishlist_shared_email.wishlist = wishlist
#         #     wishlist_shared_email.save()

#         # if wishlist.shared_emails.exists() and wishlist.visibility != WishList.SHARED:
#         #     if wishlist.visibility == WishList.PRIVATE:
#         #         msg = (
#         #             "Общие учетные записи не смогут получить доступ к вашему списку желаний, "
#         #             "потому что для них установлен частный доступ."
#         #         )
#         #     elif wishlist.visibility == WishList.PUBLIC:
#         #         msg = (
#         #             "Вы добавили общие учетные записи в свой список желаний, но видимость "
#         #             "публичная, это означает, что каждый, у кого есть ссылка, имеет к ней доступ"
#         #         )
#         #     messages.warning(self.request, msg)

#         return wishlist

#     def post(self, request, *args, **kwargs):
#         """
#         This post method will handle both the create and update view post request.
#         """
#         try:
#             self.object = self.get_object()
#         except AttributeError:
#             self.object = None

#         form = self.get_form()
#         # shared_emails_formset = WishListSharedEmailFormset(
#         #     request.POST, instance=self.object
#         # )

#         if form.is_valid():
#             wishlist = self.process_wishlist_forms(form)
#             return self.form_valid(wishlist)

#         context = self.get_context_data(form=form)
#         return self.render_to_response(context)


# class WishListUpdateView(WishListCreateUpdateViewMixin, UpdateView):
#     model = WishList
#     template_name = "oscar/customer/wishlists/wishlists_form.html"
#     active_tab = "wishlists"
#     # form_class = WishListForm
#     context_object_name = "wishlist"

#     def get_page_title(self):
#         return self.object.name

#     def get_object(self, queryset=None):
#         return get_object_or_404(
#             WishList, owner=self.request.user, key=self.kwargs["key"]
#         )

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["user"] = self.request.user
#         return kwargs

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)

#         # Invalid post response passes this to the context.
#         # if "shared_emails_formset" not in kwargs:
#         #     ctx["shared_emails_formset"] = WishListSharedEmailFormset(
#         #         instance=self.object
#         #     )

#         return ctx

#     def get_success_url(self):
#         return reverse("customer:wishlist-detail")

#     def form_valid(self, form):
#         return redirect(self.get_success_url())


# class WishListCreateView(WishListCreateUpdateViewMixin, CreateView):
#     """
#     Create a new wishlist

#     If a product ID is passed as a kwargs, then this product will be added to
#     the wishlist.
#     """

#     model = WishList
#     template_name = "oscar/customer/wishlists/wishlists_form.html"
#     active_tab = "wishlists"
#     page_title = "Создать новый список желаний"
#     # form_class = WishListForm
#     product = None

#     def dispatch(self, request, *args, **kwargs):
#         if "product_pk" in kwargs:
#             try:
#                 self.product = Product.objects.get(pk=kwargs["product_pk"])
#             except ObjectDoesNotExist:
#                 messages.error(request, "Запрошенный товар больше не существует")
#                 return redirect("wishlist-create")
#         return super().dispatch(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         ctx["product"] = self.product

#         # Invalid post response passes this to the context.
#         if "shared_emails_formset" not in kwargs:
#             ctx["shared_emails_formset"] = WishListSharedEmailFormset()

#         return ctx

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["user"] = self.request.user
#         return kwargs

#     def form_valid(self, form):
#         """
#         The form argument is actually the wishlist instance because we already saved this in
#         the post method below. This is also why we do not call form.save() here.
#         """
#         wishlist = form
#         if self.product:
#             wishlist.add(self.product)

#         return redirect(form.get_absolute_url())



# class WishListCreateWithProductView(View):
#     """
#     Create a wish list and immediately add a product to it
#     """

#     def post(self, request, *args, **kwargs):
#         product = get_object_or_404(Product, pk=kwargs["product_pk"])
#         wishlists = request.user.wishlists.all()
#         if len(wishlists) == 0:
#             wishlist = request.user.wishlists.create()
#         else:
#             # This shouldn't really happen but we default to using the first
#             # wishlist for a user if one already exists when they make this
#             # request.
#             wishlist = wishlists[0]
#         wishlist.add(product)
#         return redirect_to_referrer(request, wishlist.get_absolute_url())


# class WishListDetailView(PageTitleMixin, FormView):
# class WishListDetailView(PageTitleMixin, ListView):
#     """
#     This view acts as a DetailView for a wish list and allows updating the
#     quantities of products.

#     It is implemented as FormView because it's easier to adapt a FormView to
#     display a product then adapt a DetailView to handle form validation.
#     """

#     template_name = "oscar/customer/wishlists/wishlists_detail.html"
#     active_tab = "wishlist"
#     # form_class = LineFormset


#     def get_queryset(self):
#         return self.object.lines.all()


#     def dispatch(self, request, *args, **kwargs):
#         # pylint: disable=attribute-defined-outside-init
#         self.object = self.get_wishlist_or_404(kwargs["key"], request.user)
#         return super().dispatch(request, *args, **kwargs)

#     def get_wishlist_or_404(self, key, user):
#         wishlist = get_object_or_404(WishList, key=key)
#         if wishlist.is_allowed_to_edit(user):
#             return wishlist
#         else:
#             raise Http404

#     def get_page_title(self):
#         return self.object.name

#     # def get_form_kwargs(self):
#     #     kwargs = super().get_form_kwargs()
#     #     kwargs["instance"] = self.object
#     #     return kwargs

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         ctx["wishlist"] = self.object
#         other_wishlists = self.request.user.wishlists.exclude(pk=self.object.pk)
#         ctx["other_wishlists"] = other_wishlists
#         return ctx

#     # def form_valid(self, form):
#     #     for subform in form:
#     #         # if subform.cleaned_data["quantity"] <= 0:
#     #         #     subform.instance.delete()
#     #         # else:
#     #             subform.save()
#     #     messages.success(self.request, "Количество обновлено")
#     #     return redirect("customer:wishlists-detail", key=self.object.key)


# class WishListMoveProductToAnotherWishList(LineMixin, View):
#     def dispatch(self, request, *args, **kwargs):
#         self.fetch_line(request.user, kwargs["key"], line_pk=kwargs["line_pk"])
#         return super().dispatch(request, *args, **kwargs)

#     def get(self, request, *args, **kwargs):
#         to_wishlist = get_object_or_404(
#             WishList, owner=request.user, key=kwargs["to_key"]
#         )

#         if to_wishlist.lines.filter(product=self.line.product).count() > 0:
#             msg = " В избранном уже есть '%(title)s'" % {
#                 "title": self.product.get_title(),
#             }
#             messages.error(self.request, msg)
#         else:
#             self.line.wishlist = to_wishlist
#             self.line.save()

#             msg = ("'%(title)s' перемещен в '%(name)s'") % {
#                 "title": self.product.get_title(),
#                 "name": to_wishlist.name,
#             }
#             messages.success(self.request, msg)

#         default_url = reverse(
#             "customer:wishlists-detail", kwargs={"key": self.wishlist.key}
#         )
#         return redirect_to_referrer(self.request, default_url)


# class WishListDeleteView(PageTitleMixin, DeleteView):
#     model = WishList
#     template_name = "oscar/customer/wishlists/wishlists_delete.html"
#     active_tab = "wishlists"

#     def get_page_title(self):
#         return "Удалить список избранного"

#     def get_object(self, queryset=None):
#         return get_object_or_404(
#             WishList, owner=self.request.user, key=self.kwargs["key"]
#         )

#     def get_success_url(self):
#         messages.success(
#             self.request, "Ваш список избранного был удален"
#         )
#         return reverse("customer:wishlists-list")

