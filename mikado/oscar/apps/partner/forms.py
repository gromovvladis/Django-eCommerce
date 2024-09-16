from django import forms
from django.core.cache import cache

from oscar.core.loading import get_model

Partner = get_model("partner", "Partner")

class PartnerSelectForm(forms.Form):
    
    partner_id = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        label="ID Точки продажи",
    )

    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        partner_id_list = []

        partners_select = cache.get('partners_select')
        if not partners_select:
            partners_select = Partner.objects.prefetch_related("addresses").all()
            cache.set("partners_select", partners_select, 21600)
        
        for partner in partners_select:
            partner_id_list.append((partner.id, partner.name))


        self.fields["partner_id"].choices = partner_id_list
