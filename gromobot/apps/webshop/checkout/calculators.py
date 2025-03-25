from core import prices


class OrderTotalCalculator(object):
    """
    Calculator class for calculating the order total.
    """

    def __init__(self, request=None):
        # We store a reference to the request as the total may
        # depend on the user or the other checkout data in the session.
        # Further, it is very likely that it will as shipping method
        # always changes the order total.
        self.request = request

    def calculate(self, basket, shipping_charge=None, surcharges=None, **kwargs):
        money = basket.total

        if shipping_charge:
            money += shipping_charge.money

        if surcharges is not None:
            money += surcharges.total.money

        return prices.Price(currency=basket.currency, money=money)
