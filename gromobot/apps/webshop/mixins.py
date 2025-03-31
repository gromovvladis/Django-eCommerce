import logging

from apps.webshop.user.signals import user_registered
from core.compat import get_user_model
from core.loading import get_model
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login

User = get_user_model()
CommunicationEventType = get_model("communication", "CommunicationEventType")

logger = logging.getLogger("apps.webshop.customer")


class PageTitleMixin(object):
    """
    Passes page_title and active_tab into context, which makes it quite useful
    for the accounts views.

    Dynamic page titles are possible by overriding get_page_title.
    """

    page_title = None
    active_tab = None
    summary = None

    # Use a method that can be overridden and customised
    def get_page_title(self):
        return self.page_title

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("page_title", self.get_page_title())
        ctx.setdefault("active_tab", self.active_tab)
        ctx.setdefault("summary", self.summary)
        return ctx


class ThemeMixin(object):
    def get_template_names(self):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response() is overridden.
        """
        names = super().get_template_names()
        theme = getattr(self.request, "theme", "planet")
        return [f"webshop/themes/{theme}/{name}" for name in names]


class RegisterUserMixin(object):
    def register_user(self, form):
        """
        Create a user instance and send a new registration email (if configured
        to).
        """
        user = form.save()

        # Raise signal robustly (we don't want exceptions to crash the request
        # handling).
        user_registered.send_robust(sender=self, request=self.request, user=user)

        if getattr(settings, "SEND_REGISTRATION_EMAIL", True):
            self.send_registration_email(user)

        # We have to authenticate before login
        try:
            user = authenticate(
                username=user.email, password=form.cleaned_data["password1"]
            )
        except User.MultipleObjectsReturned:
            # Handle race condition where the registration request is made
            # multiple times in quick succession.  This leads to both requests
            # passing the uniqueness check and creating users (as the first one
            # hasn't committed when the second one runs the check).  We retain
            # the first one and deactivate the dupes.
            logger.warning(
                "Multiple users with identical email address and password"
                "were found. Marking all but one as not active."
            )
            # As this section explicitly deals with the form being submitted
            # twice, this is about the only place in Oscar where we don't
            # ignore capitalisation when looking up an email address.
            # We might otherwise accidentally mark unrelated users as inactive
            users = User.objects.filter(email=user.email)
            user = users[0]
            for u in users[1:]:
                u.is_active = False
                u.save()

        auth_login(self.request, user)

        return user


class RegisterUserPhoneMixin(object):
    def register_user(self, form):
        """
        Create a user instance and send a new registration email (if configured
        to).
        """
        user = form.save()

        # Raise signal robustly (we don't want exceptions to crash the request
        # handling).
        user_registered.send_robust(sender=self, request=self.request, user=user)

        if getattr(settings, "SEND_REGISTRATION_EMAIL", True):
            self.send_registration_email(user)

        # We have to authenticate before login
        try:
            user = authenticate(
                username=user.email, password=form.cleaned_data["password1"]
            )
        except User.MultipleObjectsReturned:
            # Handle race condition where the registration request is made
            # multiple times in quick succession.  This leads to both requests
            # passing the uniqueness check and creating users (as the first one
            # hasn't committed when the second one runs the check).  We retain
            # the first one and deactivate the dupes.
            logger.warning(
                "Multiple users with identical email address and password"
                "were found. Marking all but one as not active."
            )
            # As this section explicitly deals with the form being submitted
            # twice, this is about the only place in Oscar where we don't
            # ignore capitalisation when looking up an email address.
            # We might otherwise accidentally mark unrelated users as inactive
            users = User.objects.filter(email=user.email)
            user = users[0]
            for u in users[1:]:
                u.is_active = False
                u.save()

        auth_login(self.request, user)

        return user
