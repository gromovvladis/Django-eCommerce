from django.contrib.auth import get_user_model

from ..conf import conf
from ..models import PhoneCode
from ..utils import SmsService

User = get_user_model()


class AuthService(SmsService):
    def __init__(self, phone_number: str, code: str, *args, **kwargs):
        self.phone_number = phone_number
        self.code = code

        super().__init__()

    def process(self):
        generated_code = PhoneCode.objects.\
            filter(phone_number=self.phone_number,
                   code=self.code)\
            .first()

        if generated_code is None:
            return None, False

        user = generated_code.owner
        is_created = False
        kwargs = {conf.SMS_USER_FIELD: generated_code.phone_number}
        if user is None:
            user, is_created = User.objects.get_or_create(
                **kwargs,
                defaults={
                    "is_active": True,
                    "is_superuser": False,
                    "is_staff": False,
                    }
            )
        else:
            user.save(**kwargs)
            # user.save()

        generated_code.delete()

        return user, is_created
