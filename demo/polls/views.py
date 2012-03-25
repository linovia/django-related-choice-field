
from django import forms
from django.views.generic import FormView

from polls.models import Book, Author
from linked_choice_field.fields import LinkedModelChoiceField


class BookSelectionForm(forms.Form):
    author = forms.ModelChoiceField(queryset=Author.objects.all())
    book = LinkedModelChoiceField(
        queryset=Book.objects.all(),
        related_form_field_name='author',
        related_model_name='author')


class MyFormView(FormView):
    template_name = "example.html"
    form_class = BookSelectionForm
