from django.utils import timezone

from ..models import AuthCode


class CleanService:
    @classmethod
    def clear(cls):
        AuthCode.objects.filter(valid_to__lt=timezone.now()).delete()
