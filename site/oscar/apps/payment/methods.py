import uuid
import logging
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib import messages
from oscar.apps.order.models import PaymentEventQuantity
from oscar.apps.payment.exceptions import DebitedAmountIsNotEqualsRefunded, UnableToRefund, UnableToTakePayment
from oscar.apps.payment.models import Source, Transaction
from oscar.apps.order.models import Order, PaymentEvent, PaymentEventType

from yookassa import Refund
from yookassa import Payment

from yookassa.domain.models.receipt import Receipt
from yookassa.domain.common.confirmation_type import ConfirmationType
from yookassa.domain.request.payment_request_builder import PaymentRequestBuilder
from yookassa.domain.request import RefundRequestBuilder
from yookassa.domain.response.refund_response import RefundResponse
from yookassa.domain.response.payment_response import PaymentResponse


logger = logging.getLogger("oscar.payment")
thank_you_url = reverse_lazy('checkout:thank-you')

class PaymentManager:
    """
    Payment method will be chosen.
    """

    def __init__(self, payment_method=None):
        self.payment_method = payment_method

    def get_method(self):
        if self.payment_method =='ONLINECARD':
            return Yoomoney(self.payment_method)
        if self.payment_method == 'ELECTRON':
            return CardOffline(self.payment_method)
        else:
            return Cash(self.payment_method)
    
    @classmethod
    def get_sources(self, pk):
        return Source.objects.filter(order_id=pk).select_related("order")
    
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
        self.success_url = f"https://{settings.ALLOWED_HOSTS[0]}{thank_you_url}"
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

    def get_status(self, status_list, tnx_status, updated):
        if updated:
            return "Обновление транзакции"
        elif tnx_status == 'succeeded':
            return status_list['succeeded']
        elif tnx_status == 'canceled':
            return status_list['canceled']
        elif tnx_status == 'pending':
            return status_list['pending']

    def add_event(self, order, transaction, transaction_status_list=None, updated=False):
        event_type, __ = PaymentEventType.objects.get_or_create(
            name=self.get_status(
                transaction_status_list, 
                transaction.status,
                updated
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

        if tnx_type == 'payment':
            status_list = self.payment_status_order() 
        elif tnx_type == 'refund':
            status_list = self.refund_status_order() 
        else:
            logger.error('Неизвестный тип транзакции. Транзакция: {1}, Заказ: {2}'.format(tnx_type , order.number)) 
            return messages.error(self.request, "Неизвестный тип транзакции")
            
        new_status = self.get_status(
            status_list=status_list, 
            tnx_status=tnx_status,
            updated=False
        )

        if new_status and new_status != current_status:
            order.set_status(new_status)
    

class PaymentMethod(PaymentMethodHelper):

    def pay(self, order, amount=None, email=None):
        raise NotImplementedError(
            "A PaymentMethod must define a pay method "
        )

    def refund(self, transaction, amount=None):
        raise NotImplementedError(
            "A PaymentMethod must define a refund method "
        )

    def get_payment_api(self, pay_id):
        raise NotImplementedError(
            "A PaymentMethod must define a get_payment_api method "
        )

    def get_refund_api(self, refund_id):
        raise NotImplementedError(
            "A PaymentMethod must define a get_refund_api method "
        )

    def _check_balance(self, refund, payment, source):
        if isinstance(refund, RefundResponse) and refund.status == 'succeeded':
            refund_refunded = refund.amount.value
            source_refunded = source.amount_refunded

            if refund_refunded != source_refunded:
                logger.error(
                    "Сумма возврата заказа №(%s) не равна возврату источника оплаты. "
                    "Требуется ручная проверка. Транзакция возврата: №(%s)",
                    source.order.number,
                    refund.id,
                )
                raise DebitedAmountIsNotEqualsRefunded(
                    "Сумма возврата не равна возврату источника оплаты. "
                    "Требуется ручная проверка. На данный момент возвращено: {0} Р.".format(float(refund_refunded))
                )

        if isinstance(payment, PaymentResponse) and payment.status == 'succeeded':
            debited = payment.amount.value
            payment_refunded = payment.refunded_amount.value
            source_balance = source.amount_debited - source.amount_refunded
            transaction_balance = debited - payment_refunded

            if source_balance != transaction_balance:
                logger.error(
                    "Сумма транзакции заказа №(%s) не равна балансу источника оплаты. "
                    "Требуется ручная проверка. Транзакция оплаты: №(%s)",
                    source.order.number,
                    payment.id,
                )
                raise DebitedAmountIsNotEqualsRefunded(
                    "Сумма оплаты не равна балансу источника оплаты. "
                    "Требуется ручная проверка. На данный момент оплачено: {0} Р.".format(float(transaction_balance))
                )
            
        
        if (isinstance(payment, PaymentResponse) and payment.status == 'succeeded' and
            isinstance(refund, RefundResponse) and refund.status == 'succeeded'):

            payment_refunded = payment.refunded_amount.value
            refund_refunded = refund.amount.value

            if refund_refunded != payment_refunded:
                logger.error(
                    "Сумма возврата заказа №(%s) не равна сумме возврата в объекте оплаты. "
                    "Требуется ручная проверка. Транзакция оплаты: №(%s). Транзакция возврата: №(%s)",
                    source.order.number,
                    payment.id,
                    refund.id,
                )
                raise DebitedAmountIsNotEqualsRefunded(
                    "Сумма возврата не равна сумме прихода. "
                    "Требуется ручная проверка. На данный момент оплачено: {0} Р.".format(float(payment_refunded))
                )
            
    def update(self, source, payment=None, refund=None): 
        refund_updated = False
        payment_updated = False

        if isinstance(refund, RefundResponse):
            refund_updated = self.update_refund(refund, source)
        
        if isinstance(payment, PaymentResponse):
            payment_updated = self.update_payment(payment, source)

        self._check_balance(refund, payment, source)

        if refund_updated:
            self.change_order_status(
                tnx_status=refund.status, 
                tnx_type='refund', 
                order=source.order,
            )
        elif payment_updated:
            self.change_order_status(
                tnx_status=payment.status, 
                tnx_type='payment',  
                order=source.order,
            )

    def update_payment(self, payment, source):
        payment_transactions = self.get_transactions(source).filter(txn_type="Payment")
        existing_transactions = []

        if payment_transactions:    
            for trans in payment_transactions:
                existing_transactions.append(trans.status)

        if payment.status not in existing_transactions:
            self.create_payment_transaction(payment, source)
            return True
        else:
            return self.update_payment_transaction(payment, source)

    def create_payment_transaction(self, payment, source):
        if payment.payment_method:
            reference = payment.payment_method.title
        else:
            reference = str(source.reference) + " Payment" 

        source.new_payment(
            amount=payment.amount.value, 
            reference=reference, 
            paid=payment.paid,
            refundable=payment.refundable,
            status=payment.status,
            code=payment.id,
            receipt=payment.receipt_registration
        )

        self.add_event(order=source.order, transaction=payment, transaction_status_list=self.payment_status_list())

    def update_payment_transaction(self, payment, source):
        if payment.payment_method:
            reference = payment.payment_method.title 
        else:
            reference = str(source.reference) + " Payment"

        updated = source.update_payment(
            amount=payment.amount.value, 
            reference=reference, 
            paid=payment.paid,
            refundable=payment.refundable,
            status=payment.status,
            code=payment.id,
            receipt=payment.receipt_registration
        )

        if updated:
            self.add_event(order=source.order, transaction=payment, updated=True)
        
        return updated

    def update_refund(self, refund, source):
        refund_transactions = self.get_transactions(source).filter(txn_type="Refund")
        existing_transactions = []

        if refund_transactions:    
            for trans in refund_transactions:
                existing_transactions.append(trans.status)

        if refund.status not in existing_transactions:
            self.create_refund_transaction(refund, source)
            return True
        else:
            return self.update_refund_transaction(refund, source)

    def create_refund_transaction(self, refund, source):
        source.new_refund(
            amount=refund.amount.value, 
            reference=str(source.reference) + " Refund", 
            status=refund.status,
            code=refund.id,
            receipt=refund.receipt_registration,
        )

        self.add_event(order=source.order, transaction=refund, transaction_status_list=self.refund_status_list())

    def update_refund_transaction(self, refund, source):
        updated = source.update_refund(
            amount=refund.amount.value, 
            reference=str(source.reference) + " Refund", 
            status=refund.status,
            code=refund.id,
            receipt=refund.receipt_registration,
        )

        if updated:
            self.add_event(order=source.order, transaction=refund, updated=True)
        
        return updated

    def __str__(self) -> str:
        return self.payment_method


class Yoomoney(PaymentMethod):

    vats = {
        "NO_VAT": 1,
        "VAT_0": 2,
        "VAT_10": 3,
        "VAT_10_110": 4,
        "VAT_18": 5,
        "VAT_18_118": 6,
    }

    unit_codes = {
        "шт": "piece",
        "г": "gram",
        "кг": "kilogram",
        "т": "ton",
        "см": "centimeter",
        "дм": "decimeter",
        "м": "meter",
        "см²": "square_centimeter",
        "дм²": "square_decimeter",
        "м²": "square_meter",
        "мл": "milliliter",
        "л": "liter",
        "м³": "cubic_meter",
        "кВт·ч": "kilowatt_hour",
        "Гкал": "gigacalorie",
        "сутки": "day",
        "день": "day",
        "час": "hour",
        "минута": "minute",
        "секунда": "second",
        "КБ": "kilobyte",
        "МБ": "megabyte",
        "ГБ": "gigabyte",
        "ТБ": "terabyte",
    }

    def pay(self, order, amount=None, email=None):
        try:
            if amount is None:
                amount = order.total
            
            if email is None:
                email = order.user.email

            receipt = Receipt()
            receipt.customer = {
                "phone": str(order.user.username),
                **({"email": email} if email else {}),
            }
            receipt.tax_system_code = 4
            receipt.items = self._receipt_items(order)

            builder = PaymentRequestBuilder()
            builder.set_amount({"value": amount.money, "currency": amount.currency}) \
                .set_confirmation({"type": ConfirmationType.REDIRECT, "return_url": self.success_url}) \
                .set_capture(True) \
                .set_description("Заказ №" + str(order.number)) \
                .set_metadata({"orderNumber": order.number}) \
                .set_receipt(receipt) \
                .set_merchant_customer_id(order.user.id) \
                
            request = builder.build()
            pay = Payment.create(request, uuid.uuid4())

        except Exception as e:
            raise UnableToTakePayment(f'Ошибка создания платежа ЮКасса {e}')

        return pay

    def refund(self, transaction, amount=None):
        try:
            payment_id = transaction.code
            order = transaction.source.order
            if payment_id:
                email = order.user.email

                if amount is None:
                    amount = transaction.amount

                receipt = Receipt()
                receipt.customer = {
                    "phone": str(order.user.username),
                    **({"email": email} if email else {}),
                }
                receipt.tax_system_code = 4
                receipt.items = self._receipt_items(order)

                item_list = []
                for line in order.lines.all():
                    item = {
                        'description': line.name,
                        'quantity': line.quantity,
                            'amount': {
                                "value": line.line_price,
                                "currency": order.currency,
                            },
                        'vat_code': 4,
                    }
                    item_list.append(item)
                
                receipt.items = item_list
                    
                builder = RefundRequestBuilder()
                builder.set_payment_id(payment_id) \
                    .set_description("Возврат по заказу №" + str(order.number)) \
                    .set_amount({"value": amount, "currency": transaction.source.currency}) \
                    .set_receipt(receipt) \

                request = builder.build()
                refund_responce = Refund.create(request)
                transaction.refundable = False
                transaction.save()
        except Exception as e:
            try:
                error = e.response.content
            except Exception as e:
                error = e
            raise UnableToRefund(f'Невозможно произвести возврат. Причина: {error}')

        return refund_responce
    
    def get_payment_api(self, pay_id):
        try:
            responce = Payment.find_one(pay_id)
        except Exception:
            return None
        
        return responce

    def get_refund_api(self, refund_id):
        try:
            responce = Refund.find_one(refund_id)
        except Exception:
            return None
        
        return responce
      
    def _receipt_items(self, order):
        item_list = []
        for line in order.lines.all():
            item = {
                'description': line.get_full_name(),
                'quantity': line.quantity,
                'amount': {
                    "value": line.line_price,
                    "currency": order.currency,
                },
                'measure': self.unit_codes.get(line.product.get_product_class().measure_name, "piece"),
                'payment_subject': "commodity",
                'payment_mode': "full_payment",
                'vat_code': self.vats.get(line.tax_code, 6),
            }
            item_list.append(item)

        if order.shipping > 0:
            item_list.append({     
                "description": "Доставка",
                "quantity": 1,
                'amount': {
                    "value": order.shipping,
                    "currency": order.currency,
                },
                "measure": "piece",
                'payment_subject': "service",
                'payment_mode': "full_payment",
                'vat_code': 6,
            })

        return item_list


# переделай
class Cash(PaymentMethod):
    def pay(self, order, amount=None, email=None):
        pass

    def refund(self, transaction, amount=None):
        pass

    def update(self, source, payment=None, refund=None):
        pass

    def create_payment_transaction(self, payment, source):
        pass 
      
    def create_refund_transaction(self, refund, source):
        pass
    
 
class CardOffline(PaymentMethod):
    def pay(self, order, amount=None):
        pass

    def refund(self, transaction, amount=None):
        pass
