from django import forms

from oscar.core.loading import get_class, get_classes, get_model
from oscar.forms.widgets import DateTimePickerInput, ImageInput, ThumbnailInput

Partner = get_model("partner", "Partner")

class ProductClassForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pylint: disable=no-member
        remote_field = self._meta.model._meta.get_field("options").remote_field
        self.fields["options"].widget = RelatedMultipleFieldWidgetWrapper(
            self.fields["options"].widget, remote_field
        )

    class Meta:
        model = Partner
        fields = ["name", "requires_shipping", "track_stock", "options"]
