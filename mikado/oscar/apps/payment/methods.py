import uuid
from django.urls import reverse_lazy
from django.conf import settings
import logging
from oscar.apps.order.abstract_models import PaymentEventQuantity
from oscar.apps.payment.exceptions import DebitedAmountIsNotEqualsRefunded, UnableToRefund, UnableToTakePayment
from oscar.apps.payment.models import Source, Transaction
from oscar.apps.order.models import Order, PaymentEvent, PaymentEventType
from django.contrib import messages
from django.contrib.sites.models import Site

from yookassa import Refund
from yookassa import Payment

from yookassa.domain.models.receipt import Receipt
from yookassa.domain.common.confirmation_type import ConfirmationType
from yookassa.domain.request.payment_request_builder import PaymentRequestBuilder
from yookassa.domain.request import RefundRequestBuilder
from yookassa.domain.response.refund_response import RefundResponse
from yookassa.domain.response.payment_response import PaymentResponse


logger = logging.getLogger("oscar.payment")

class PaymentManager:
    """
    Payment method will be chosen.
    """

    def __init__(self, payment_method=None):
        self.payment_method = payment_method

    def get_method(self):
        if self.payment_method == 'SBP':
            return Yoomoney(self.payment_method)
        if self.payment_method == 'CARD':
            return Sber(self.payment_method)
        if self.payment_method == 'COURIER-CARD':
            return CourierCard(self.payment_method)
        else:
            return CourierCash(self.payment_method)
    
    @classmethod
    def get_sources(self, pk):
        return Source.objects.filter(order_id=pk)
    
    @classmethod
    def get_last_source(self, pk:int):
        sources = self.get_sources(pk)
        return sources.last()

    @classmethod
    def get_paid_money(self, pk:int):
        sources = self.get_sources(pk)
        sum = 0
        for source in sources:
            sum += source.amount_debited

        return sum
    
    @classmethod
    def get_available_for_refund_money(self, pk:int):
        sources = self.get_sources(pk)
        sum = 0
        for source in sources:
            sum += source.amount_available_for_refund

        return sum
    
    @classmethod
    def get_refunded_money(self, pk:int):
        sources = self.get_sources(pk)
        sum = 0
        for source in sources:
            sum += source.amount_refunded

        return sum

    @classmethod
    def get_allocated_money(self, pk:int):
        order_total = Order.objects.get(id=pk).total
        sum =  order_total - self.get_paid_money(pk)

        return sum
        

class PaymentMethodHelper(object):

    def __init__(self, payment_method):
        url_domain = Site.objects.get_current().domain
        url_path = reverse_lazy("checkout:thank-you")
        success_url_path = url_domain + url_path
        self.success_url = success_url_path
        self.payment_method = payment_method
    

    def get_method(self):
        return self.payment_method


    def get_transactions(self, payment_source):
        return Transaction.objects.filter(source_id=payment_source.id)


    def payment_status_list(self):
        return settings.PAYMENT_STATUS


    def refund_status_list(self):
        return settings.REFUND_STATUS


    def payment_status_order(self):
        return settings.PAYMENT_ORDER_STATUS


    def refund_status_order(self):
        return settings.REFUND_ORDER_STATUS


    def get_status(self, status_list, status):

        if status == 'succeeded':
            return status_list['succeeded']
        elif status == 'canceled':
            return status_list['canceled']

        return status_list['pending']


    def add_event(self, transaction, transaction_status_list, order):
        event_type, __ = PaymentEventType.objects.get_or_create(
            name=self.get_status(
                transaction_status_list, 
                transaction.status
            )
        )
        event = PaymentEvent(event_type=event_type, amount=transaction.amount.value, reference=transaction.id)
        event.order = order
        event.save()
        for line in order.lines.all():
            PaymentEventQuantity.objects.create(
                event=event, line=line, quantity=line.quantity
            )

    
    def change_order_status(self, tnx_status, tnx_type, order):
        
        current_status = order.status

        status_to_change = [
            settings.OSCAR_INITIAL_ONLINE_PAYMENT_ORDER_STATUS, 
            settings.OSCAR_INITIAL_ORDER_STATUS,
            settings.OSCAR_PAID_ONLINE_PAYMENT_ORDER_STATUS
        ]

        if current_status in status_to_change:

            if tnx_type == 'payment':
                status_list = self.payment_status_order() 
            elif tnx_type == 'refund':
                status_list = self.refund_status_order() 
            else:
                return messages.error(self.request, "Неизвестный тип транзакции")
                
            new_status = self.get_status(
                status_list=status_list, 
                status=tnx_status
            )

            if new_status != current_status:
                order.set_status(new_status)

            return new_status
        

class AbstractPaymentMethod(PaymentMethodHelper):



    def __init__(self, payment_method):
        super().__init__(payment_method)
    
    #override pass
    def pay(self, order, amount=None, email=None):
        return None

    #override pass
    def refund(self, transaction, amount=None):
        pass

    #override pass
    def get_payment_api(self, pay_id):
        pass

    #override pass
    def get_refund_api(self, refund_id):
        pass

    # isinstance PaymentResponse
    def create_payment_transaction(self, payment, source):
        
        if isinstance(payment, PaymentResponse):

            payment_transactions = self.get_transactions(source).filter(txn_type="Payment")
            existing_transactions = []

            if payment_transactions:    
                for trans in payment_transactions:
                    existing_transactions.append(trans.status)

            if payment.status not in existing_transactions:

                reference = str(source.reference) + " Payment" 
                if payment.payment_method:
                    reference = payment.payment_method.title

                source.new_payment(
                    amount=payment.amount.value, 
                    reference=reference, 
                    paid=payment.paid,
                    refundable=payment.refundable,
                    status=payment.status,
                    code=payment.id,
                    receipt=payment.receipt_registration
                )

                order = source.order
                self.add_event(payment, self.payment_status_list() , order)
                return self.change_order_status(
                    tnx_status=payment.status, 
                    tnx_type='payment', 
                    order=order,
                )
            
    # isinstance RefundResponse
    def create_refund_transaction(self, refund, source):
        
        if isinstance(refund, RefundResponse):

            refund_transactions = self.get_transactions(source).filter(txn_type="Refund")
            existing_transactions = []

            if refund_transactions:    
                for trans in refund_transactions:
                    existing_transactions.append(trans.status)

            if refund.status not in existing_transactions:

                source.new_refund(
                    amount=refund.amount.value, 
                    reference=str(source.reference) + " Refund", 
                    status=refund.status,
                    code=refund.id,
                    receipt=refund.receipt_registration,
                )

                order = source.order
                self.add_event(refund, self.refund_status_list() , order)
                return self.change_order_status(
                    tnx_status=refund.status, 
                    tnx_type='refund', 
                    order=order,
                )


    def update(self, source, payment=None, refund=None): 

        old_status = source.order.status
        new_status = ""
        debited = 0
        payment_responce_refunded = 0
        refund_responce_refunded = 0
        pay_id = 'X' 
        refund_id = 'X' 
    
        if isinstance(payment, PaymentResponse):
            new_status = self.create_payment_transaction(payment, source)
            pay_id = payment.id
            if payment.status == 'succeeded':
                debited = payment.amount.value
                payment_responce_refunded = payment.refunded_amount.value

        if isinstance(refund, RefundResponse):
            new_status = self.create_refund_transaction(refund, source)
            refund_id = refund.id
            refund_responce_refunded = refund.amount.value

        source_balance = source.amount_debited - source.amount_refunded
        transaction_balance = debited - payment_responce_refunded

        if source_balance != transaction_balance or refund_responce_refunded != payment_responce_refunded:
            logger.error(
                "Сумма возврата заказа №(%s) не равна сумме прихода. Требуется ручная проверка. Транзакция оплаты: №(%s). Транзакция возврата: №(%s)"
                "Order #%s: unable to take payment (%s) - restoring basket",
                source.order.number,
                pay_id,
                refund_id,
            )
            raise DebitedAmountIsNotEqualsRefunded("Сумма возврата не равна сумме прихода. Требуется ручная проверка. На данный момент оплачено: {0} Р.".format(float(transaction_balance)))
        
        return new_status or old_status
        
    def __str__(self) -> str:
        return self.payment_method


    class Meta:
        abstract = True


class Yoomoney(AbstractPaymentMethod):

    def pay(self, order, amount=None, email=None):

        try:
            customer_dict = {}
            item_list = []
            
            phone = order.user.username
            client_id = order.user.id
            if not email:
                email = order.user.email
            description = "Заказ №" + str(order.number)

            if amount is None:
                amount = order.total
            if email:
                customer_dict['email'] = email       
            if phone:
                customer_dict['phone'] = phone

            receipt = Receipt()
            receipt.customer = customer_dict
            receipt.tax_system_code = 1

            for line in order.basket.lines.all():
                item = {
                    'description': line.title,
                    'quantity': line.quantity,
                        'amount': {
                            "value": line.line_price_incl_discounts,
                            "currency": order.currency,
                        },
                    'vat_code': 4,
                }
                item_list.append(item)
            
            receipt.items = item_list
            builder = PaymentRequestBuilder()
            builder.set_amount({"value": amount.money, "currency": amount.currency}) \
                .set_confirmation({"type": ConfirmationType.REDIRECT, "return_url": self.success_url}) \
                .set_capture(True) \
                .set_description(description) \
                .set_metadata({"orderNumber": order.number}) \
                .set_receipt(receipt) \
                .set_merchant_customer_id(client_id) \
                # .set_payment_method_data({"type": "sbp"})
                
            request = builder.build()
            pay = Payment.create(request, uuid.uuid4())

        except Exception as e:
            raise UnableToTakePayment('Не возможно произвести оплату')

        return pay

     
    def refund(self, transaction, amount=None):

        try:
            payment_id = transaction.code
            order = transaction.source.order
            description = "Возврат по заказу №" + str(order.number)
            if not amount:
                amount = transaction.amount
            if payment_id:

                customer_dict = {}
                item_list = []
                
                phone = order.user.username
                email = order.user.email
                description = "Заказ №" + str(order.number)

                if amount is None:
                    amount = order.total
                if email:
                    customer_dict['email'] = email       
                if phone:
                    customer_dict['phone'] = phone

                receipt = Receipt()
                receipt.customer = customer_dict
                receipt.tax_system_code = 1

                for line in order.basket.lines.all():
                    item = {
                        'description': line.title,
                        'quantity': line.quantity,
                            'amount': {
                                "value": line.line.line_price_incl_discounts,
                                "currency": order.currency,
                            },
                        'vat_code': 4,
                    }
                    item_list.append(item)
                
                receipt.items = item_list
                    
                builder = RefundRequestBuilder()
                builder.set_payment_id(payment_id) \
                    .set_description(description) \
                    .set_amount({"value": amount, "currency": transaction.source.currency}) \
                    .set_receipt(receipt) \

                request = builder.build()
                refund_responce = Refund.create(request)
    
        except Exception as e:
            raise UnableToRefund('Не возможно произвести возврат')

        return refund_responce
    

    def get_payment_api(self, pay_id):
        
        try:
            responce = Payment.find_one(pay_id)
        except Exception as e:
            return None
        
        return responce


    def get_refund_api(self, refund_id):

        try:
            responce = Refund.find_one(refund_id)
        except Exception as e:
            return None
        
        return responce
    

class CourierCash(AbstractPaymentMethod):
    pass


class CourierCard(AbstractPaymentMethod):
    pass


class Sber(AbstractPaymentMethod):
    """
    Payment method
    """
    pass
    
