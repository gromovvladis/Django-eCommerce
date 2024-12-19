class TaxNotKnown(Exception):
    """
    Exception for when a t-inclusive price is requested but we don't know
    what the t applicable is (yet).
    """


class Price(object):
    """
    Simple price class that encapsulates a price and its tax information

    """

    def __init__(self, currency, money, tax_code=None):
        self.currency = currency
        self.money = money
        self.tax_code = tax_code

    def __repr__(self):
        return "%s(currency=%r, money=%r)" % (
            self.__class__.__name__,
            self.currency,
            self.money,
        )

    def __eq__(self, other):
        """
        Two price objects are equal if currency, price.excl_tax and tax match.
        """
        return (
            self.currency == other.currency
            and self.money == other.money
        )

    def __add__(self, other):
        if self.currency != other.currency:
            raise ValueError("Cannot add prices with different currencies.")

        return Price(
            currency=self.currency,
            money=self.money + other.money,
            tax_code=self.tax_code,
        )

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)
