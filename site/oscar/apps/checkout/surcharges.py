from decimal import Decimal as D
from oscar.core import prices


class BaseSurcharge:
    """
    Surcharge interface class

    This is the superclass to the classes in surcharges.py. This allows using all
    surcharges interchangeably (aka polymorphism).

    The interface is all properties.
    """

    def calculate(self, basket, **kwargs):
        raise NotImplementedError


class PercentageCharge(BaseSurcharge):
    name = "Процентная надбавка"
    code = "percentage-surcharge"

    def __init__(self, percentage):
        self.percentage = percentage

    def calculate(self, basket, **kwargs):
        if not basket.is_empty:
            shipping_charge = kwargs.get("shipping_charge")

            if shipping_charge is not None:
                total = basket.total + shipping_charge.money
            else:
                total = basket.total

            return prices.Price(
                currency=basket.currency,
                money=total * self.percentage / 100,
            )
        else:
            return prices.Price(currency=basket.currency, money=D("0.0"))


class FlatCharge(BaseSurcharge):
    name = "Фиксированная доплата"
    code = "flat-surcharge"

    def __init__(self, money=None):
        self.money = money

    def calculate(self, basket, **kwargs):
        return prices.Price(currency=basket.currency, money=self.money)
