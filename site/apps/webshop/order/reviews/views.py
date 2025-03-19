from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from apps.webshop.order.reviews.signals import order_review_added
from core.loading import get_class, get_classes, get_model

PageTitleMixin, ThemeMixin = get_classes(
    "webshop.mixins", ["PageTitleMixin", "ThemeMixin"]
)
OrderReviewForm = get_class("webshop.catalogue.reviews.forms", "OrderReviewForm")

Order = get_model("order", "Order")
OrderReview = get_model("order_reviews", "OrderReview")
Line = get_model("wishlists", "Line")
Product = get_model("catalogue", "Product")


class OrderFeedbackAvailibleListView(PageTitleMixin, ThemeMixin, ListView):
    """
    Customer order history
    """

    context_object_name = "orders"
    template_name = "customer/feedbacks/feedbacks_order_list.html"
    paginate_by = settings.ORDERS_PER_PAGE
    model = Order
    page_title = "Оставить отзыв"
    active_tab = "feedback"

    def get_queryset(self):
        """
        Return Queryset of :py:class:`Order <apps.webshop.order.models.Order>`
        instances for the currently authenticated user.
        """
        return self.model.objects.filter(
            Q(user=self.request.user),
            Q(status=settings.SUCCESS_ORDER_STATUS),
            ~Q(reviews__isnull=False),  # Проверяем, что связанных отзывов нет
        )

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["content_open"] = True
        ctx["summary"] = "profile"
        return ctx


class OrderFeedbackListView(PageTitleMixin, ThemeMixin, ListView):
    """
    Customer order history
    """

    context_object_name = "reviews"
    template_name = "customer/feedbacks/feedbacks_list.html"
    paginate_by = settings.ORDERS_PER_PAGE
    model = OrderReview
    page_title = "Отзывы"
    active_tab = "feedback"

    def get_queryset(self):
        """
        Return Queryset of :py:class:`Order <apps.webshop.order.models.Order>`
        instances for the currently authenticated user.
        """
        return self.model.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["content_open"] = True
        ctx["summary"] = "profile"
        return ctx


class AddOrderFeedbackView(PageTitleMixin, ThemeMixin, CreateView):
    context_object_name = "order_review"
    template_name = "customer/feedbacks/feedbacks_add.html"
    model = OrderReview
    order_model = Order
    form_class = OrderReviewForm
    page_title = "Создание отзыва"
    active_tab = "feedback"
    view_signal = order_review_added
    success_url = reverse_lazy("customer:feedbacks")

    def dispatch(self, request, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self.order = get_object_or_404(self.order_model, number=kwargs["order_number"])
        if not self.order.is_review_permitted(request.user):
            if self.order.has_review_by(request.user):
                message = "Вы уже оставили отзыв об этом заказе."
            else:
                message = "Вы не можете оставить отзыв об этом заказе."
            messages.warning(self.request, message)
            return redirect(self.order.get_absolute_url())

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["order"] = self.order
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["order"] = self.order
        ctx["summary"] = "profile"
        ctx["content_open"] = True
        return ctx

    def send_signal(self, request, response, review):
        self.view_signal.send(
            sender=self,
            review=review,
            user=request.user,
            request=request,
            response=response,
        )
