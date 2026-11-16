from django import forms
from .models import Crew


class AssignmentForm(forms.Form):
    crew = forms.ModelChoiceField(Crew.objects.filter(is_active=True), label='Бригада', empty_label='Выберите бригаду')
