from django import forms
from oscar.core.loading import get_class
from oscar.forms.widgets import DatePickerInput

GeneratorRepository = get_class("dashboard.reports.utils", "GeneratorRepository")


class ReportForm(forms.Form):
    generators = GeneratorRepository().get_report_generators()
    type_choices = []
    for generator in generators:
        type_choices.append((generator.code, generator.description))

    date_from = forms.DateField(
        label="Дата с", required=False, widget=DatePickerInput(attrs={"class": "dateinput"}),
    )
    date_to = forms.DateField(
        label="Дата до",
        help_text="Отчет включает эту дату",
        required=False,
        widget=DatePickerInput(attrs={"class": "dateinput"}),
    )
    report_type = forms.ChoiceField(
        widget=forms.Select(),
        choices=type_choices,
        label="Тип отчета",
        help_text="Выбранный диапазон дат используется только в отчетах о предложениях и заказах",
    )
    download = forms.BooleanField(label="Скачать", required=False)

    def clean(self):
        date_from = self.cleaned_data.get("date_from", None)
        date_to = self.cleaned_data.get("date_to", None)
        if (
            all([date_from, date_to])
            and self.cleaned_data["date_from"] > self.cleaned_data["date_to"]
        ):
            raise forms.ValidationError("Дата начала должна предшествовать дате окончания.")
        
        return self.cleaned_data
