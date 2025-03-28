import datetime

from core.utils import datetime_combine
from django import forms


class OrderSearchForm(forms.Form):

    date_range = forms.CharField(
        required=False,
        label=("Даты заказов"),
    )
    order_number = forms.CharField(required=False, label="Номер заказа")

    def clean(self):
        if self.is_valid() and not any(
            [
                self.cleaned_data["date_range"],
                self.cleaned_data["order_number"],
            ]
        ):
            raise forms.ValidationError("Требуется хотя бы одно поле.")
        return super().clean()

    def description(self):
        """
        Uses the form's data to build a useful description of what orders
        are listed.
        """
        if not self.is_bound or not self.is_valid():
            return
            # return "Все заказы"
        else:
            date_range = self.cleaned_data["date_range"].split(" - ")
            date_from = None
            date_to = None

            if len(date_range) > 0 and date_range[0]:
                date_from = datetime.datetime.strptime(date_range[0], "%d.%m.%Y").date()

            if len(date_range) > 1 and date_range[1]:
                date_to = datetime.datetime.strptime(date_range[1], "%d.%m.%Y").date()

            order_number = self.cleaned_data["order_number"]
            return self._orders_description(date_from, date_to, order_number)

    def _orders_description(self, date_from, date_to, order_number):
        if date_from and date_to:
            if order_number:
                desc = (
                    "Заказы с %(date_from)s до "
                    "%(date_to)s и номером заказа содержащий: "
                    "%(order_number)s"
                )
            else:
                desc = "Заказы c %(date_from)s до %(date_to)s"
        elif date_from:
            if order_number:
                desc = (
                    "Заказы с %(date_from)s и "
                    "номер заказа, содержащий %(order_number)s"
                )
            else:
                desc = "Заказы с %(date_from)s"
        elif date_to:
            if order_number:
                desc = (
                    "Заказы до %(date_to)s и "
                    "номер заказа, содержащий %(order_number)s"
                )
            else:
                desc = "Заказы до %(date_to)s"
        elif order_number:
            desc = "Заказы с номером, содержащий %(order_number)s"
        else:
            return None
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "order_number": order_number,
        }
        return desc % params

    def get_filters(self):
        date_range = self.cleaned_data["date_range"].split(" - ")
        date_from = None
        date_to = None

        if len(date_range) > 0 and date_range[0]:
            date_from = datetime.datetime.strptime(date_range[0], "%d.%m.%Y").date()

        if len(date_range) > 1 and date_range[1]:
            date_to = datetime.datetime.strptime(date_range[1], "%d.%m.%Y").date()

        order_number = self.cleaned_data["order_number"]
        kwargs = {}
        if date_from:
            kwargs["date_placed__gte"] = datetime_combine(date_from, datetime.time.min)
        if date_to:
            kwargs["date_placed__lte"] = datetime_combine(date_to, datetime.time.max)
        if order_number:
            kwargs["number__contains"] = order_number
        return kwargs
