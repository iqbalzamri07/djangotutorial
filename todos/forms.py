from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Todo


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ["username", "email"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
        }


class TodoForm(forms.ModelForm):
    """Todo create/edit form using start/end dates (not due_datetime)."""

    class Meta:
        model = Todo
        fields = ["title", "notes", "start_date", "end_date"]
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional notes or description...",
                }
            ),
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
