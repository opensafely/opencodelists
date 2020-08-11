import csv
from io import StringIO

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import Codelist, CodelistVersion, Reference, SignOff


class FormSetHelper(FormHelper):
    """
    FormHelper for use with Crispy Forms and FormSets

    When using Crispy Forms helpers with FormSet their layout is applied to the
    Forms but attributes to the FormSet, so we need to pass the FormHelper
    instance into the crispy_forms templatetag in the view.

    https://django-crispy-forms.readthedocs.io/en/latest/crispy_tag_formsets.html#formsets
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_csrf = True
        self.form_tag = False


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = [
            "text",
            "url",
        ]


class SignOffForm(forms.ModelForm):
    date = forms.DateField(widget=forms.TextInput(attrs={"type": "date"}))

    class Meta:
        model = SignOff
        fields = [
            "user",
            "date",
        ]


class CSVValidationMixin:
    def clean_csv_data(self):
        data = self.cleaned_data["csv_data"].read().decode("utf-8")

        reader = csv.reader(StringIO(data))
        num_columns = len(next(reader))  # expected to be headers
        errors = [i for i, row in enumerate(reader) if len(row) != num_columns]

        if errors:
            msg = "Incorrect number of columns on row {}"
            raise forms.ValidationError(
                [
                    forms.ValidationError(msg.format(i + 1), code=f"row{i + 1}")
                    for i in errors
                ]
            )

        return data


class CodelistForm(forms.ModelForm, CSVValidationMixin):
    csv_data = forms.FileField(label="CSV data")

    class Meta:
        model = Codelist
        fields = ["name", "coding_system_id", "description", "methodology", "csv_data"]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        super().__init__(*args, **kwargs)


class CodelistVersionForm(forms.Form, CSVValidationMixin):
    csv_data = forms.FileField(label="CSV data")

    class Meta:
        model = CodelistVersion
        fields = ["csv_data"]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        super().__init__(*args, **kwargs)