from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    ListView,
)

from oscar.core.loading import get_class, get_model

Order = get_model("order", "Order")
OrderReview = get_model("customer", "OrderReview")
Line = get_model("wishlists", "Line")
Product = get_model("catalogue", "Product")
PageTitleMixin = get_class("customer.mixins", "PageTitleMixin")
OrderReviewForm = get_class("catalogue.reviews.forms", "OrderReviewForm")


class OrderFeedbackAvailibleListView(PageTitleMixin, ListView):
    """
    Customer order history
    """
    context_object_name = "orders"
    template_name = "oscar/customer/feedbacks/feedbacks_order_list.html"
    paginate_by = settings.OSCAR_ORDERS_PER_PAGE
    model = Order
    page_title = "Оставить отзыв"
    active_tab = "feedback"

    def get_queryset(self):
        """
        Return Queryset of :py:class:`Order <oscar.apps.order.models.Order>`
        instances for the currently authenticated user.
        """
        return self.model.objects.filter(
            Q(user=self.request.user),
            Q(status="Завершён"),
            ~Q(reviews__isnull=False)  # Проверяем, что связанных отзывов нет
        )

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["content_open"] = True
        ctx["summary"] = "Профиль"
        return ctx


class OrderFeedbackListView(PageTitleMixin, ListView):
    """
    Customer order history
    """
    context_object_name = "reviews"
    template_name = "oscar/customer/feedbacks/feedbacks_list.html"
    paginate_by = settings.OSCAR_ORDERS_PER_PAGE
    model = OrderReview
    page_title = "Отзывы"
    active_tab = "feedback"

    def get_queryset(self):
        """
        Return Queryset of :py:class:`Order <oscar.apps.order.models.Order>`
        instances for the currently authenticated user.
        """        
        return self.model.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["content_open"] = True
        ctx["summary"] = "Профиль"
        return ctx

            
class AddOrderFeedbackView(PageTitleMixin, CreateView): 
    context_object_name = "order_review"
    template_name = "oscar/customer/feedbacks/feedbacks_add.html"
    model = OrderReview
    order_model = Order
    form_class = OrderReviewForm
    page_title = "Создание отзыва"
    active_tab = "feedback"
    success_url = reverse_lazy("customer:feedbacks")

    def dispatch(self, request, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self.order = get_object_or_404(
            self.order_model, number=kwargs["order_number"]
        )
        if not self.order.is_review_permitted(request.user):
            if self.order.has_review_by(request.user):
                message = "Вы уже оставили отзыв об этом заказе!"
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
        ctx["title"] = "Создание отзыва"
        ctx["summary"] = "Профиль"
        ctx["content_open"] = True
        return ctx

