from django.utils import timezone
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured

from oscar.core.compat import get_user_model
from ..sms_auth.services import AuthService

User = get_user_model()

if hasattr(User, "REQUIRED_FIELDS"):
    if not (User.USERNAME_FIELD == "username" or "username" in User.REQUIRED_FIELDS):
        raise ImproperlyConfigured(
            "PhoneBack: Your User model must have an username field with blank=False"
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
        
        if not username:
            if "username" not in kwargs or kwargs["username"] is None:
                return None
            username = kwargs["username"]
        if not password:
            if "password" not in kwargs or kwargs["password"] is None:
                return None
            password = kwargs["password"]

        return self._authenticate(username, password)

