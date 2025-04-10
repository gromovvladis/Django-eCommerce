from apps.webshop.catalogue.reviews.signals import product_review_added
from core.loading import get_classes, get_model
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView

PageTitleMixin, ThemeMixin = get_classes(
    "webshop.mixins", ["PageTitleMixin", "ThemeMixin"]
)
ProductReviewForm, SortReviewsForm = get_classes(
    "webshop.catalogue.reviews.forms", ["ProductReviewForm", "SortReviewsForm"]
)

ProductReview = get_model("product_reviews", "ProductReview")
Product = get_model("catalogue", "Product")


class CreateProductReview(PageTitleMixin, ThemeMixin, CreateView):
    template_name = "catalogue/reviews/review_form.html"
    model = ProductReview
    product_model = Product
    form_class = ProductReviewForm
    view_signal = product_review_added
    page_title = "Оставить отзыв"
    summary = "profile"

    def dispatch(self, request, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self.product = get_object_or_404(
            self.product_model, pk=kwargs["product_pk"], is_public=True
        )
        # check permission to leave review
        if not self.product.is_review_permitted(request.user):
            if self.product.has_review_by(request.user):
                message = "Вы уже оставили отзыв об этом товаре!"
            else:
                message = "Вы не можете оставить отзыв об этом товаре."
            messages.warning(self.request, message)
            return redirect(self.product.get_absolute_url())

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = self.product
        context["content_open"] = True
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["product"] = self.product
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        self.send_signal(self.request, response, self.object)
        return response

    def get_success_url(self):
        messages.success(self.request, "Спасибо за ваш отзыв!")
        return reverse_lazy("customer:order-list")

    def send_signal(self, request, response, review):
        self.view_signal.send(
            sender=self,
            review=review,
            user=request.user,
            request=request,
            response=response,
        )


class ProductReviewList(PageTitleMixin, ThemeMixin, ListView):
    """
    Browse reviews for a product
    """

    template_name = "catalogue/reviews/review_list.html"
    context_object_name = "reviews"
    summary = "profile"
    model = ProductReview
    product_model = Product
    paginate_by = settings.REVIEWS_PER_PAGE

    def get(self, request, *args, **kwargs):
        if self.request.user.is_staff:
            return super().get(request, *args, **kwargs)
        else:
            return redirect(reverse("customer:profile-view"))

    def get_queryset(self):
        qs = self.model.objects.filter(product=self.kwargs["product_pk"])
        # pylint: disable=attribute-defined-outside-init
        self.form = SortReviewsForm(self.request.GET)
        if self.request.GET and self.form.is_valid():
            sort_by = self.form.cleaned_data["sort_by"]
            if sort_by == SortReviewsForm.SORT_BY_RECENCY:
                return qs.order_by("-date_created")
        return qs.order_by("-score")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = get_object_or_404(
            self.product_model, slug=self.kwargs["product_slug"], is_public=True
        )
        context["form"] = self.form
        return context

    def get_page_title(self):
        return f"Отзывы на товар {_product.name}"
