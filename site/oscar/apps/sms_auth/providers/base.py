from typing import Protocol
from smsaero import SmsAero
from ..conf import conf

def sms_decorator(func, to):
    from ..models import SMSMessage

    def wrapper():
        result = func()
        if result:
            cost = result.get('cost')
            SMSMessage.objects.create(phone_number=to, cost=cost)
            return 'secceded'

    return wrapper


class SMSProviderClass(Protocol):
    to: str
    message: str
    conf: dict

    def send_sms(self):
        pass


class SMSProvider:
    def __getattribute__(self, item):
        element = super().__getattribute__(item)
        if callable(element) and item == "send_sms":
            return sms_decorator(element, self.to)

        return element

    def __init__(self, to, message):
        self.to = to
        self.message = message
        self.conf = conf

    def send_sms(self):
        raise NotImplementedError()


TYPE_SEND = 2

class SmsAeroException(Exception):
    pass


class Smsaero(SMSProvider):

    def send_sms(self):
        """
        Send sms and return results.

                Parameters:
                        phone (int): Phone number
                        message (str): Message to send

                Returns:
                        data (dict): API request result
        """
        signature = self.conf.SMS_PROVIDER_FROM

        # api = SmsAero(
        #     email=self.conf.SMS_PROVIDER_LOGIN,
        #     api_key=self.conf.SMS_PROVIDER_API_TOKEN,
        # )
        # res = api.send(
        #     number=self.to,
        #     text=self.message, 
        #     date_send=None, 
        #     callback_url=None,
        # )
        # assert res.get('success'), res.get('message')
        # return res.get('data')

        return {'cost': 12}
