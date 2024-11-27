# pylint: disable=attribute-defined-outside-init
import datetime
from decimal import Decimal as D
from decimal import InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Sum, fields
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView, UpdateView, DeleteView, CreateView, View

from oscar.apps.dashboard.orders.forms import NewSourceForm, NewTransactionForm
from oscar.apps.order import exceptions as order_exceptions
from oscar.apps.payment.exceptions import DebitedAmountIsNotEqualsRefunded, PaymentError
from oscar.apps.payment.methods import PaymentManager
from oscar.apps.payment.models import Source
from oscar.core.compat import UnicodeCSVWriter
from oscar.core.loading import get_class, get_model
from oscar.core.utils import datetime_combine, format_datetime
from oscar.views import sort_queryset
from oscar.views.generic import BulkEditMixin

import logging
logger = logging.getLogger("oscar.dashboard")

Store = get_model("store", "Store")
Transaction = get_model("payment", "Transaction")
SourceType = get_model("payment", "SourceType")
Order = get_model("order", "Order")
OrderNote = get_model("order", "OrderNote")
ShippingAddress = get_model("order", "ShippingAddress")
Line = get_model("order", "Line")
ShippingEventType = get_model("order", "ShippingEventType")
PaymentEventType = get_model("order", "PaymentEventType")
EventHandlerMixin = get_class("order.mixins", "EventHandlerMixin")
OrderStatsForm = get_class("dashboard.orders.forms", "OrderStatsForm")
OrderSearchForm = get_class("dashboard.orders.forms", "OrderSearchForm")
OrderNoteForm = get_class("dashboard.orders.forms", "OrderNoteForm")
ShippingAddressForm = get_class("dashboard.orders.forms", "ShippingAddressForm")
OrderStatusForm = get_class("dashboard.orders.forms", "OrderStatusForm")


class TelegramAdminView(View):
    pass

class TelegramErrorsView(View):
    pass

class TelegramCouriersView(View):
    pass
