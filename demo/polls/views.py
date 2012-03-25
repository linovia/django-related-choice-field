
from django import forms
from django.views.generic import FormView

from polls.models import Book, Author
from linked_choice_field.fields import LinkedModelChoiceField
from linked_choice_field.fields import LinkedModelMultipleChoiceField


class BookSelectionForm(forms.Form):
    author = forms.ModelChoiceField(queryset=Author.objects.all())
    book = LinkedModelChoiceField(
        queryset=Book.objects.all(),
        related_form_field_name='author',
        related_model_name='author')


class MultiBookSelectionForm(forms.Form):
    author = forms.ModelChoiceField(queryset=Author.objects.all())
    book = LinkedModelMultipleChoiceField(
        queryset=Book.objects.all(),
        related_form_field_name='author',
        related_model_name='author')


class MyFormView(FormView):
    template_name = "example.html"
    form_class = BookSelectionForm
    success_url = '/'


class MySecondFormView(FormView):
    template_name = "example.html"
    form_class = MultiBookSelectionForm
    success_url = '/2/'
