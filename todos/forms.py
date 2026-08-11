from django import forms
from .models import Todo


class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ["title", "due_datetime"]
        widgets = {
            # Use HTML5 datetime-local to make the timetable input easy.
            "due_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }