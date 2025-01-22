from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.template import engines
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template

from oscar.apps.communication.managers import CommunicationTypeManager
from oscar.core.compat import AUTH_USER_MODEL
from oscar.models.fields import AutoSlugField


class Email(models.Model):
    """
    This is a record of an email sent to a customer.
    """

    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emails",
        verbose_name="Пользователь",
        null=True,
    )
    email = models.EmailField("Email", null=True, blank=True)
    subject = models.TextField("Тема", max_length=255)
    body_text = models.TextField("Тело Text")
    body_html = models.TextField("Тело HTML", blank=True)
    date_sent = models.DateTimeField("Дата отправки", auto_now_add=True)

    class Meta:
        app_label = "communication"
        ordering = ["-date_sent"]
        verbose_name = "Email"
        verbose_name_plural = "Emails"

    def __str__(self):
        if self.user:
            return ("Email для пользователя %(user)s с темой '%(subject)s'") % {
                "user": self.user.get_username(),
                "subject": self.subject,
            }
        else:
            return ("Email для пользователя %(email)s с темой '%(subject)s'") % {
                "email": self.email,
                "subject": self.subject,
            }


class CommunicationEventType(models.Model):
    """
    A 'type' of communication.  Like an order confirmation email.
    """

    #: Code used for looking up this event programmatically.
    # e.g. PASSWORD_RESET. AutoSlugField uppercases the code for us because
    # it's a useful convention that's been enforced in previous Oscar versions
    code = AutoSlugField(
        "Код",
        max_length=128,
        unique=True,
        populate_from="name",
        separator="_",
        uppercase=True,
        editable=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z_][0-9A-Z_]*$",
                message=(
                    "Код может содержать только заглавные буквы (A-Z)"
                    "цифры и подчеркивания, и не могут начинаться с цифры."
                ),
            )
        ],
        help_text="Код, используемый для программного поиска этого события",
    )

    #: Name is the friendly description of an event for use in the admin
    name = models.CharField("Имя", max_length=255, db_index=True)

    # We allow communication types to be categorised
    # For backwards-compatibility, the choice values are quite verbose
    ORDER_RELATED = "Order"
    USER_RELATED = "User"
    CATEGORY_CHOICES = (
        (ORDER_RELATED, "Связанное с заказом"),
        (USER_RELATED, "Связанное с пользователем"),
    )

    category = models.CharField(
        "Категория", max_length=255, default=ORDER_RELATED, choices=CATEGORY_CHOICES
    )

    # Template content for emails
    # NOTE: There's an intentional distinction between None and ''. None
    # instructs Oscar to look for a file-based template, '' is just an empty
    # template.
    email_subject_template = models.CharField(
        "Шаблон темы электронного письма", max_length=255, blank=True, null=True
    )
    email_body_template = models.TextField(
        "Шаблон тела электронного письма", blank=True, null=True
    )
    email_body_html_template = models.TextField(
        "HTML-шаблон тела электронного письма",
        blank=True,
        null=True,
        help_text="HTML шаблон",
    )

    # Template content for SMS messages
    sms_template = models.CharField(
        "SMS шаблон",
        max_length=170,
        blank=True,
        null=True,
        help_text="SMS шаблон",
    )

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_updated = models.DateTimeField("Дата изменения", auto_now=True)

    objects = CommunicationTypeManager()

    # File templates
    email_subject_template_file = "oscar/communication/emails/commtype_%s_subject.txt"
    email_body_template_file = "oscar/communication/emails/commtype_%s_body.txt"
    email_body_html_template_file = "oscar/communication/emails/commtype_%s_body.html"
    sms_template_file = "oscar/communication/sms/commtype_%s_body.txt"

    class Meta:
        app_label = "communication"
        ordering = ["name"]
        verbose_name = "Событие уведомления"
        verbose_name_plural = "События уведомлений"

    def get_messages(self, ctx=None):
        """
        Return a dict of templates with the context merged in

        We look first at the field templates but fail over to
        a set of file templates that follow a conventional path.
        """
        code = self.code.lower()

        # Build a dict of message name to Template instances
        templates = {
            "subject": "email_subject_template",
            "body": "email_body_template",
            "html": "email_body_html_template",
            "sms": "sms_template",
        }
        for name, attr_name in templates.items():
            field = getattr(self, attr_name, None)
            if field is not None:
                # Template content is in a model field
                templates[name] = engines["django"].from_string(field)
            else:
                # Model field is empty - look for a file template
                template_name = getattr(self, "%s_file" % attr_name) % code
                try:
                    templates[name] = get_template(template_name)
                except TemplateDoesNotExist:
                    templates[name] = None

        # Pass base URL for serving images within HTML emails
        if ctx is None:
            ctx = {}
        ctx["static_base_url"] = getattr(settings, "OSCAR_STATIC_BASE_URL", None)

        messages = {}
        for name, template in templates.items():
            # pylint: disable=no-member
            messages[name] = template.render(ctx) if template else ""

        # Ensure the email subject doesn't contain any newlines
        messages["subject"] = messages["subject"].replace("\n", "")
        messages["subject"] = messages["subject"].replace("\r", "")

        return messages

    def __str__(self):
        return self.name

    def is_order_related(self):
        return self.category == self.ORDER_RELATED

    def is_user_related(self):
        return self.category == self.USER_RELATED


class Notification(models.Model):
    recipient = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )

    # Not all notifications will have a sender.
    sender = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    order = models.ForeignKey("order.Order", on_delete=models.CASCADE, null=True)

    # HTML is allowed in this field as it can contain links
    subject = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    body = models.TextField()

    INBOX, ARCHIVE = "Inbox", "Archive"
    location_choices = ((INBOX,"Входящие"), (ARCHIVE, "Архив"))
    location = models.CharField(max_length=32, choices=location_choices, default=INBOX)

    SUCCESS, INFO, WARNING, CANCELED  = "Success", "Info", "Warning", "Canceled"
    status_choices = ((SUCCESS,"Успешно"), (INFO, "Инфо"), (WARNING, "Предупреждение"), (CANCELED, "Отмена"))
    status = models.CharField(max_length=32, choices=status_choices, default=INFO)

    date_sent = models.DateTimeField(auto_now_add=True)
    date_read = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = "communication"
        ordering = ("-date_sent",)
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return self.subject

    def archive(self):
        self.location = self.ARCHIVE
        self.save()

    archive.alters_data = True

    @property
    def is_read(self):
        return self.date_read is not None


class WebPushSubscription(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    endpoint = models.URLField()
    p256dh = models.TextField()
    auth = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "communication"
        db_table = "communication_webpush"
        verbose_name = "Подписка на WebPush"
        verbose_name_plural = "Подписки на WebPush"

    def __str__(self):
        return f"Subscription for {self.user or 'Anonymous'}"
