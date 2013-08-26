
from django import forms
from django.views.generic import FormView

from .models import Book, Author
from related_choice_field.fields import RelatedModelChoiceField
from related_choice_field.fields import RelatedModelMultipleChoiceField


class BookSelectionForm(forms.Form):
    author = forms.ModelChoiceField(queryset=Author.objects.all())
    book = RelatedModelChoiceField(
        queryset=Book.objects.all(),
        related_form_field_name='author',
        related_model_name='author')


class MultiBookSelectionForm(forms.Form):
    author = forms.ModelChoiceField(queryset=Author.objects.all())
    book = RelatedModelMultipleChoiceField(
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
