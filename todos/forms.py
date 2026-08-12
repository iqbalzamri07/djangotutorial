from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import Subtask, Tag, Todo


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
        fields = [
            "title",
            "notes",
            "priority",
            "tags",
            "start_date",
            "end_date",
            "recurrence",
            "recurrence_until",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "What needs doing?"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "Optional notes...",
                }
            ),
            "priority": forms.Select(),
            "tags": forms.CheckboxSelectMultiple(),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "recurrence_until": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Tag.ensure_defaults()
        self.fields["tags"].queryset = Tag.objects.all()
        self.fields["tags"].required = False
        self.fields["priority"].required = False

    def clean(self):
        cleaned = super().clean()
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")
        recurrence = cleaned.get("recurrence")
        recurrence_until = cleaned.get("recurrence_until")

        if not cleaned.get("priority"):
            cleaned["priority"] = Todo.PRIORITY_MEDIUM

        if start_date and not end_date:
            cleaned["end_date"] = start_date
        elif end_date and not start_date:
            cleaned["start_date"] = end_date
        elif start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date cannot be before start date.")

        if recurrence and not cleaned.get("start_date"):
            self.add_error("start_date", "Recurring tasks need a start date.")
        if recurrence_until and cleaned.get("start_date") and recurrence_until < cleaned["start_date"]:
            self.add_error("recurrence_until", "Repeat until cannot be before the start date.")

        return cleaned


class SubtaskForm(forms.ModelForm):
    class Meta:
        model = Subtask
        fields = ["title", "completed", "order"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Checklist item..."}),
            "order": forms.HiddenInput(),
        }


SubtaskFormSet = inlineformset_factory(
    Todo,
    Subtask,
    form=SubtaskForm,
    extra=3,
    can_delete=True,
)
