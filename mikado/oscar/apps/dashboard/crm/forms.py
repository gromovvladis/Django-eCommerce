from django import forms

from oscar.apps.dashboard.widgets import RelatedMultipleFieldWidgetWrapper
from oscar.core.loading import get_class, get_classes, get_model
from oscar.forms.widgets import DateTimePickerInput, ImageInput, ThumbnailInput

Partner = get_model("partner", "Partner")


class CRMProductForm(forms.Form):
    partner = forms.ChoiceField(
        label="Точка продажи", required=False, choices=()
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        partners = self.partner_choices()
        self.fields["partner"].choices = partners
        if partners:
            self.fields["partner"].initial = partners[0][0]

    def partner_choices(self):
        return tuple(
            [(src.evotor_id, src.name) for src in Partner.objects.filter(evotor_id__isnull=False, is_active=True)]
        )