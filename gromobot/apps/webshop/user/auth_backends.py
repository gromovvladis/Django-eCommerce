from apps.sms.services.auth import AuthService
from core.compat import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

User = get_user_model()

if hasattr(User, "REQUIRED_FIELDS"):
    if not (User.USERNAME_FIELD == "username" or "username" in User.REQUIRED_FIELDS):
        raise ImproperlyConfigured(
            "PhoneBack: Your User model must have a username field with blank=False"
        )


class PhoneBackend(ModelBackend):
    # pylint: disable=keyword-arg-before-vararg
    def _authenticate(self, username, password):
        # Check if we're dealing with an phone number and code
        if len(username) != 12 or len(password) != 4:
            return None

        try:
            user, is_created = AuthService.execute(phone_number=username, code=password)
            user.last_login = timezone.now()
            user.save()
            return user
        except Exception:
            return None

    def authenticate(self, username=None, password=None, *args, **kwargs):
        # Проверка на наличие username и password, если они не переданы
        if not username:
            username = kwargs.get("username", None)
        if not password:
            password = kwargs.get("password", None)

        if not username or not password:
            return None

        return self._authenticate(username, password)
