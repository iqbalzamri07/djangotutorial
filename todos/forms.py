from django import forms
from .models import Todo


class TodoForm(forms.ModelForm):
    """Todo create/edit form using start/end dates (not due_datetime)."""

    class Meta:
        model = Todo
        fields = ["title", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")

        if start_date and not end_date:
            cleaned["end_date"] = start_date
        elif end_date and not start_date:
            cleaned["start_date"] = end_date
        elif start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date cannot be before start date.")

        return cleaned
