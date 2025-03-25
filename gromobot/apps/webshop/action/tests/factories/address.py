import factory

from core.loading import get_model
from phonenumber_field.phonenumber import PhoneNumber

__all__ = [
    "UserAddressFactory",
]


class UserAddressFactory(factory.django.DjangoModelFactory):
    title = "Dr"
    first_name = "Barry"
    last_name = "Barrington"
    line1 = "1 King Road"
    line4 = "London"
    postcode = "SW1 9RE"
    phone_number = PhoneNumber.from_string("+49 351 3296645")
    user = factory.SubFactory("apps.webshop.test.factories.UserFactory")

    class Meta:
        model = get_model("address", "UserAddress")
