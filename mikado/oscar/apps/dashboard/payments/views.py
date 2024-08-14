from decimal import Decimal as D
from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import DetailView, UpdateView, DeleteView, CreateView
from django_tables2 import SingleTableView
import requests

from oscar.apps.dashboard.orders.forms import NewSourceForm, NewTransactionForm
from oscar.apps.payment.exceptions import DebitedAmountIsNotEqualsRefunded
from oscar.apps.payment.methods import PaymentManager
from oscar.apps.payment.models import Source
from oscar.core.compat import get_user_model
from oscar.core.loading import get_classes, get_model
from yookassa import Payment, Refund, Receipt

import logging
logger = logging.getLogger("oscar.dashboard")

User = get_user_model()
Transaction = get_model("payment", "Transaction")
Order = get_model("order", "Order")
PaymentListTable, RefundListTable = get_classes("dashboard.payments.tables", ["PaymentListTable", "RefundListTable"])


class TransactionsListView(SingleTableView):
    context_object_name = 'transactions'
    template_name = 'oscar/dashboard/payments/payments_list.html'
    paginate_by = settings.OSCAR_DASHBOARD_PAYMENTS_PER_PAGE

    def get_queryset(self):

        status = self.request.GET.get('status')
        date_gte = self.request.GET.get('date_gte')
        date_lte = self.request.GET.get('date_lte')

        params = {"limit": 100}
        
        if status:
            params['status'] = status

        if date_lte:
            params['created_at.lte'] = date_lte

        if date_gte:
            params['created_at.gte'] = date_gte

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
        context['title'] = 'Список платежей Yookassa'
        context['status_options'] = [('pending', 'Платеж создан и ожидает действий от пользователя'), ('waiting_for_capture', 'Платеж оплачен, деньги авторизованы и ожидают списания'), ('succeeded', 'Платеж успешно завершен'), ('canceled', 'Платеж отменен')]
        return context


class RefundsListView(TransactionsListView):
    table_class = RefundListTable
    model = Refund

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список возвратов Yookassa'
        context['status_options'] = [('pending', 'Возврат создан'), ('succeeded', 'Возврат успешно завершен'), ('canceled', 'Возврат отменен')]
        return context
   

class PaymentDetailView(DetailView):
    template_name = 'oscar/dashboard/payments/payment_detail.html'
    model = Payment
    
    def get(self, request, *args, **kwargs):
        try:
            payment_data = self.model.find_one(kwargs['pk'])
            if payment_data.merchant_customer_id:
                user = User.objects.get(id=payment_data.merchant_customer_id)      

        except Exception as e:
            raise Http404(f"Payment not found: {str(e)}")
        
        return render(request, self.template_name, {'payment': payment_data, 'user': user, 'title': 'Информация о платеже'})


class RefundDetailView(DetailView):
    template_name = 'oscar/dashboard/payments/refund_detail.html'
    model = Refund

    def get(self, request, *args, **kwargs):
        try:
            refund_data = self.model.find_one(kwargs['pk'])
        except Exception as e:
            raise Http404(f"Payment not found: {str(e)}")
        
        return render(request, self.template_name, {'refund': refund_data, 'title': 'Информация о возврате'})



class UpdateSourceView(UpdateView):
    """
    Обновить информацию о транзациях для конкретного СОРСА
    """

    model = Source

    def get(self, request, *args, **kwargs):
        """
        Fetch the latest status from docdata.
        """
        self.object = self.get_object()


        # Perform update.
        try:
            payment_method = PaymentManager(self.object.reference).get_method()
            payment = payment_method.get_payment_api(self.object.payment_id)
            refund = payment_method.get_refund_api(self.object.refund_id)
            payment_method.update(
                source=self.object, 
                payment=payment, 
                refund=refund,
            )
            logger.info("Способ оплаты был обновлен пользователем {0}".format(request.user.id)) 
        except DebitedAmountIsNotEqualsRefunded as e:
            messages.error(request, e)
        except Exception as e:
            messages.error(request, "Ошибка обновления. Попробуйте позже")
        else:
            messages.info(request, u"Информация об источнике оплаты успешно обновлена")

        return HttpResponseRedirect(reverse('dashboard:order-detail', args=(self.object.order.number,)))


class DeleteSourceView(DeleteView):
    """
    Удалить источние оплты, если в нет нет оплаченых платежей
    """

    model = Source
    template_name_suffix = "_confirm_delete_source"
    template_name = 'oscar/dashboard/orders/confirm_delete_source.html'

    def post(self, request, *args, **kwargs):
        """
        Cancel the object in Source
        """
        self.object = self.get_object()
        payment_method = self.object.source_type.name
        order_number = self.object.order.number
        self.object.delete()

        logger.info("Способ оплаты был удален пользователем {0}".format(request.user.id)) 
        messages.info(request, (u'Способ оплаты "{payment_method}" был успешно удален.').format(payment_method=payment_method))

        return HttpResponseRedirect(reverse('dashboard:order-detail', args=(order_number,)))


class AddSourceView(CreateView):
    
    template_name = "oscar/dashboard/orders/add_source.html"
    model = Source
    order_model = Order
    form_class = NewSourceForm

    def dispatch(self, request, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self.order = get_object_or_404(
            self.order_model, number=kwargs["number"]
        )
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
            form_edited = form.save(commit=False)
            form_edited.amount_debited = D(0)
            form_edited.amount_refunded = D(0)
            form_edited.refundable = False
            form_edited.paid = False
            form_edited.order = form.order
            form_edited.currency = form.order.currency
            form_edited.reference = form.instance.source_type.code
            form_edited.save()
            messages.success(self.request, "Способ оплаты был успешно добавлен!")
        except Exception as e:
            messages.error(self.request, "Ошибка при добавлении способа оплаты!")
    
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('dashboard:order-detail', args=(self.order.number,))


class AddTransactionView(CreateView):

    template_name = "oscar/dashboard/orders/add_transaction.html"
    model = Transaction
    order_model = Order
    form_class = NewTransactionForm

    def dispatch(self, request, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self.order = get_object_or_404(
            self.order_model, number=kwargs["number"]
        )
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
            source = form.cleaned_data.get('source')
            amount = form.cleaned_data.get('amount')
            reference = "Добавлено пользователем:" + str(self.request.user.name) + "(id=" + str(self.request.user.id) + ")"
            status = form.cleaned_data.get('status')
            paid = form.cleaned_data.get('paid')
            code = form.cleaned_data.get('code')
            txn_type = form.cleaned_data.get('txn_type')

            if txn_type == 'Refund':
                source.new_refund(amount, reference, status, paid, code)
            elif txn_type == 'Payment':
                source.new_payment(amount, reference, status, paid, code)

            messages.success(self.request, "Новая транзакция была успешно добавлена!")
        except Exception as e:
            messages.error(self.request, "Невозможно добавить транзакцию!")
    
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('dashboard:order-detail', args=(self.order.number,))


class RefundTransactionView(DetailView):
    """
    Отменить транзакцию и подать на возврат
    """

    model = Transaction
    template_name_suffix = "_confirm_refund"
    template_name = 'oscar/dashboard/orders/confirm_refund.html'

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
        pk = self.kwargs.get('pk')
        code = self.kwargs.get('code')
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
        self.object = self.get_object()
        amount = request.POST.get('amount')

        try:
            payment_method = PaymentManager(self.object.source.reference).get_method()
            
            refund = payment_method.refund(
                transaction=self.object, 
                amount=amount,
            )
            payment_method.create_refund_transaction(refund, self.object.source)

            logger.info('Транзакция №{0} была отменена пользователем #{1}'.format(self.object.id ,request.user.id)) 
        except Exception as e:
            messages.error(request, "Возврат не удался")
        else:
            messages.info(request, "Возврат совершен!")

        return HttpResponseRedirect(reverse('dashboard:order-detail', args=(self.object.source.order.number,)))
    