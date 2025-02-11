import logging
from decimal import Decimal as D
from datetime import datetime
from yookassa import Payment, Refund

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import DetailView, UpdateView, DeleteView, CreateView
from django_tables2 import SingleTableView
from django.views.generic.edit import FormView

from oscar.apps.payment.exceptions import DebitedAmountIsNotEqualsRefunded
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_classes, get_model

NewSourceForm = get_class("dashboard.orders.forms", "NewSourceForm")
NewTransactionForm = get_class("dashboard.orders.forms", "NewTransactionForm")
PaymentManager = get_class("payment.methods", "PaymentManager")
PaymentListTable, RefundListTable = get_classes(
    "dashboard.payments.tables", ["PaymentListTable", "RefundListTable"]
)

User = get_user_model()
Transaction = get_model("payment", "Transaction")
Order = get_model("order", "Order")
Source = get_model("payment", "Source")
SourceType = get_model("payment", "SourceType")

logger = logging.getLogger("oscar.dashboard")


class TransactionsListView(SingleTableView):
    template_name = "oscar/dashboard/payments/transaction_list.html"
    context_table_name = "transactions"
    paginate_by = settings.OSCAR_DASHBOARD_PAYMENTS_PER_PAGE

    def get_queryset(self):
        self.search_filters = []
        status = self.request.GET.get("status")
        date_gte = self.request.GET.get("date_gte")
        date_lte = self.request.GET.get("date_lte")

        params = {"limit": 100}

        if status:
            params["status"] = status
            statuses = {
                "succeeded": " Успешно",
                "canceled": "Отменен",
                "pending": "Обрабатывается",
                "waiting_for_capture": "Требует действий",
            }
            self.search_filters.append(
                (
                    ('Статус соответствует "%s"' % statuses.get(status)),
                    (("status", status),),
                )
            )

        if date_gte:
            params["created_at.gte"] = (
                datetime.strptime(date_gte, "%d.%m.%Y").date().isoformat()
            )
            self.search_filters.append(
                (
                    ("Размещено после {start_date}").format(start_date=date_gte),
                    (("date_gte", date_gte),),
                )
            )

        if date_lte:
            params["created_at.lte"] = (
                datetime.strptime(date_lte, "%d.%m.%Y").date().isoformat()
            )
            self.search_filters.append(
                (
                    ("Размещено до {end_date}").format(end_date=date_lte),
                    (("date_lte", date_lte),),
                )
            )

        try:
            res = self.model.list(params=params).items
        except Exception as e:
            res = []
            logger.error("Error Yokassa payments list - %s" % str(e))

        return res


class PaymentsListView(TransactionsListView):
    table_class = PaymentListTable
    model = Payment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_filters"] = self.search_filters
        context["title"] = "Список платежей Yookassa"
        context["status_options"] = [
            ("succeeded", "Платеж успешно завершён"),
            ("canceled", "Платеж отменен"),
            ("pending", "Платеж создан и ожидает оплаты от пользователя"),
            (
                "waiting_for_capture",
                "Платеж оплачен, деньги авторизованы и ожидают списания",
            ),
        ]
        return context


class RefundsListView(TransactionsListView):
    table_class = RefundListTable
    model = Refund

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_filters"] = self.search_filters
        context["title"] = "Список возвратов Юкасса"
        context["status_options"] = [
            ("succeeded", "Возврат успешно завершён"),
            ("canceled", "Возврат отменен"),
            ("pending", "Возврат в процессе обработки"),
        ]
        return context


class PaymentDetailView(DetailView):
    template_name = "oscar/dashboard/payments/payment_detail.html"
    model = Payment

    def get(self, request, *args, **kwargs):
        try:
            payment_data = self.model.find_one(kwargs["pk"])
            if payment_data.merchant_customer_id:
                user = User.objects.get(id=payment_data.merchant_customer_id)

        except Exception as e:
            raise Http404(f"Payment not found: {str(e)}")

        return render(
            request,
            self.template_name,
            {"payment": payment_data, "user": user, "title": "Информация о платеже"},
        )


class RefundDetailView(DetailView):
    template_name = "oscar/dashboard/payments/refund_detail.html"
    model = Refund

    def get(self, request, *args, **kwargs):
        try:
            refund_data = self.model.find_one(kwargs["pk"])
        except Exception as e:
            raise Http404(f"Payment not found: {str(e)}")

        return render(
            request,
            self.template_name,
            {"refund": refund_data, "title": "Информация о возврате"},
        )


class UpdateSourceView(UpdateView):
    """
    Обновить информацию о транзакциях для конкретного СОРСА
    """

    model = Source

    def get(self, request, *args, **kwargs):
        """
        Fetch the latest status from docdata.
        """
        self.object = self.get_object()

        # Perform update.
        try:
            for trx in self.object.transactions.all():
                pay_id = trx.payment_id
                if pay_id:
                    source_reference = trx.source.reference
                    payment_method = PaymentManager(source_reference, request.user).get_method()
                    payment_api = payment_method.get_payment_api(pay_id)
                    refund_id = trx.refund_id
                    refund_api = payment_method.get_refund_api(refund_id)
                    payment_method.update(trx.source, payment_api, refund_api)
                    logger.info(
                        "Способ оплаты был обновлен пользователем {0}".format(
                            request.user.id
                        )
                    )
        except DebitedAmountIsNotEqualsRefunded as e:
            logger.error(e)
            messages.error(request, e)
        except Exception as e:
            logger.error(
                "Ошибка при обновлении транзакции: №{1}, Пользователь: {2}, Ошибка: {3}".format(
                    self.object, self.request.user.id, e
                )
            )
            messages.error(request, "Ошибка обновления. Попробуйте позже")
        else:
            messages.info(request, "Информация об источнике оплаты успешно обновлена")

        return HttpResponseRedirect(
            reverse("dashboard:order-detail", args=(self.object.order.number,))
        )


class DeleteSourceView(DeleteView):
    """
    Удалить источние оплты, если в нет нет оплаченых платежей
    """

    model = Source
    template_name_suffix = "_confirm_delete_source"
    template_name = "oscar/dashboard/orders/confirm_delete_source.html"

    def post(self, request, *args, **kwargs):
        """
        Cancel the object in Source
        """
        self.object = self.get_object()
        payment_method = self.object.source_type.name
        order_number = self.object.order.number
        self.object.delete()

        logger.info(
            "Способ оплаты был удален пользователем {0}".format(request.user.id)
        )
        messages.info(
            request,
            ('Способ оплаты "{payment_method}" был успешно удален.').format(
                payment_method=payment_method
            ),
        )

        return HttpResponseRedirect(
            reverse("dashboard:order-detail", args=(order_number,))
        )


class AddSourceView(FormView):

    template_name = "oscar/dashboard/orders/add_source.html"
    form_class = NewSourceForm

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, number=kwargs["number"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["order"] = self.order
        return kwargs

    def form_valid(self, form):
        try:
            source_code = form.cleaned_data["source_type"]

            for val, label in settings.WEBSHOP_PAYMENT_CHOICES:
                if val == source_code:
                    source_name = label
                    break

            source_type, is_created = SourceType.objects.get_or_create(
                code=source_code, name=source_name
            )

            new_source = Source(
                amount_allocated=form.cleaned_data["amount_allocated"],
                amount_debited=D(0),
                amount_refunded=D(0),
                refundable=False,
                paid=False,
                order=self.order,
                currency=self.order.currency,
                reference=form.cleaned_data["source_type"],
                source_type=source_type,
            )
            if is_created:
                source_type.save()
            new_source.save()
            messages.success(self.request, "Способ оплаты был успешно добавлен!")
        except Exception as e:
            logger.error(
                "Ошибка при добавлении способа оплаты для заказа: №{1}, Пользователь: {2}, Ошибка: {3}".format(
                    self.order, self.request.user.id, e
                )
            )
            messages.error(self.request, f"Ошибка при добавлении способа оплаты: {e}")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("dashboard:order-detail", args=(self.order.number,))


class AddTransactionView(CreateView):
    template_name = "oscar/dashboard/orders/add_transaction.html"
    model = Transaction
    order_model = Order
    form_class = NewTransactionForm

    def dispatch(self, request, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self.order = get_object_or_404(self.order_model, number=kwargs["number"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["order"] = self.order
        return kwargs

    def form_valid(self, form):
        try:
            source = form.cleaned_data.get("source")
            amount = form.cleaned_data.get("amount")
            reference = "Сотрудник " + str(self.request.user.username)
            status = form.cleaned_data.get("status")
            paid = form.cleaned_data.get("paid")
            code = form.cleaned_data.get("code")
            txn_type = form.cleaned_data.get("txn_type")

            if txn_type == "Refund":
                source.new_refund(
                    amount=amount,
                    reference=reference,
                    status=status,
                    paid=paid,
                    refund_id=code,
                )
            elif txn_type == "Payment":
                source.new_payment(
                    amount=amount,
                    reference=reference,
                    status=status,
                    paid=paid,
                    payment_id=code,
                )

            messages.success(self.request, "Новая транзакция была успешно добавлена!")
        except Exception as e:
            logger.error(
                "Ошибка создание транзакции для источника оплаты: {1}, Пользователь: {2}, Ошибка: {3}".format(
                    source, self.request.user.id, e
                )
            )
            messages.error(self.request, "Невозможно добавить транзакцию!")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("dashboard:order-detail", args=(self.order.number,))


class RefundTransactionView(DetailView):
    """
    Отменить транзакцию и подать на возврат
    """

    model = Transaction
    template_name_suffix = "_confirm_refund"
    template_name = "oscar/dashboard/orders/confirm_refund.html"

    def get_object(self, queryset=None):
        """
        Return the object the view is displaying.

        Require `self.queryset` and a `pk` or `slug` argument in the URLconf.
        Subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        # Next, try looking up by primary key.
        pk = self.kwargs.get("pk")
        code = self.kwargs.get("code")
        if pk is not None:
            queryset = queryset.filter(pk=pk)

        # Next, try looking up by slug.
        if code is not None and pk is None:
            queryset = queryset.filter(code=code)

        # If none of those are defined, it's an error.
        if pk is None and code is None:
            raise AttributeError(
                "Generic detail view %s must be called with either an object "
                "pk or a slug in the URLconf." % self.__class__.__name__
            )

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj

    def post(self, request, *args, **kwargs):
        """
        Fetch the latest status from docdata.
        """
        try:
            self.object = self.get_object()
            amount = D(request.POST.get("amount"))
            source_reference = self.object.source.reference
            payment_method = PaymentManager(source_reference, request.user).get_method()

            payment_method.refund(
                transaction=self.object,
                amount=amount,
            )

            # payment_method.change_order_status(
            #     tnx_status=refund.status,
            #     tnx_type="refund",
            #     order=self.object.source.order,
            # )

            logger.info(
                "Транзакция №{0} была отменена пользователем. Деньги вернулись клиенту #{1}".format(
                    self.object.id, request.user.id
                )
            )
        except Exception as e:
            logger.error(
                "Ошибка возврата транзакции №{0}, Пользователь: {1}, Ошибка: {2}".format(
                    self.object.id, request.user.id, e
                )
            )
            messages.error(request, "Возврат не удался.")
        else:
            messages.info(request, "Возврат совершен!")

        return HttpResponseRedirect(
            reverse("dashboard:order-detail", args=(self.object.source.order.number,))
        )
