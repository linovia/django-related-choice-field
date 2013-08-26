from __future__ import print_function, division, absolute_import, unicode_literals

from itertools import chain
from django.forms.util import flatatt
from django.utils.safestring import mark_safe

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import escape, conditional_escape
from django.utils.datastructures import MultiValueDict, MergeDict
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import MultipleHiddenInput
try:
    from django.utils.encoding import force_text
except:
    from django.utils.encoding import force_unicode as force_text


MEDIA_JS = """
    <script type="text/javascript" defer="defer">
        function cascadeSelect(parent, child){
                var childOptions = child.find('option:not(.static)');
                    child.data('options',childOptions);

                parent.change(function(){
                    childOptions.remove();
                    child.append(
                        child.data('options').filter('.sub_' + this.value)
                    ).change();
                })

                childOptions.not('.static, .sub_' + parent.val()).remove();
        }

        $(function(){
            %(source)sSelect = $('#id_%(source)s');
            %(destination)sSelect = $('#id_%(destination)s');

            cascadeSelect(%(source)sSelect, %(destination)sSelect);
        });
    </script>
"""


class RelatedSelect(forms.Select):
    allow_multiple_selected = False

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        output = ['<select%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, [value], name=name)
        if options:
            output.append(options)
        output.append('</select>')
        output.append(MEDIA_JS % {
            'source': self.related_form_field_name,
            'destination': name
        })

        return mark_safe('\n'.join(output))

    def render_options(self, choices, selected_choices, name=None):
        # Normalize to strings.
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append('<optgroup label="%s">' %
                    escape(force_text(option_value)))
                for option in option_label:
                    output.append(
                        self.render_option(selected_choices, *option))
                output.append('</optgroup>')
            else:
                output.append(self.render_option(
                    selected_choices, option_value, option_label))
        return '\n'.join(output)

    def render_option(self, selected_choices, option_value, option_label):
        if option_value:
            option_value, related_option_value = option_value
            related_option_str = 'sub_%s' % related_option_value
        else:
            related_option_value = None
            related_option_str = 'static'
        option_value = force_text(option_value)

        option_tuple = (option_value, force_text(related_option_value))
        if option_tuple in selected_choices:
            selected_html = ' selected="selected"'
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_tuple)
        else:
            selected_html = ''

        value = '<option value="%s"%s class="%s">%s</option>' % (
            escape(option_value), selected_html, escape(related_option_str),
            conditional_escape(force_text(option_label)))
        return value

    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data and this widget's name, returns the value
        of this widget. Returns None if it's not provided.
        """
        return (
            data.get(name, None),
            data.get(self.related_form_field_name, None)
        )


class RelatedModelChoiceField(forms.ModelChoiceField):
    widget = RelatedSelect

    def __init__(self,
            related_form_field_name=None, related_model_name=None,
            *args, **kwargs):
        self.related_form_field_name = related_form_field_name
        self.related_model_name = related_model_name
        super(RelatedModelChoiceField, self).__init__(*args, **kwargs)
        self.widget.related_form_field_name = self.related_form_field_name

    def clean(self, value):
        """
        Validates the given value and returns its "cleaned" value as an
        appropriate Python object.

        Raises ValidationError for any errors.
        """
        value, related_value = value
        value = super(RelatedModelChoiceField, self).clean(value)
        if int(related_value) != \
            getattr(value, '%s_id' % self.related_model_name):
            raise ValidationError('Value does not match %s value.' %
                (self.related_form_field_name,))
        return value

    def prepare_value(self, value):
        if hasattr(value, '_meta'):
            if self.to_field_name:
                return (
                    value.serializable_value(self.to_field_name),
                    getattr(value, '%s_id' % self.related_model_name, None),
                )
            else:
                return (
                    value.pk,
                    getattr(value, '%s_id' % self.related_model_name, None)
                )
        return super(RelatedModelChoiceField, self).prepare_value(value)


class MultipleRelatedSelect(RelatedSelect):
    allow_multiple_selected = True

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        final_attrs = self.build_attrs(attrs, name=name)
        output = ['<select multiple="multiple"%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, value)
        if options:
            output.append(options)
        output.append('</select>')
        return mark_safe('\n'.join(output))

    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data and this widget's name, returns the value
        of this widget. Returns None if it's not provided.
        """
        related_value = data.get(self.related_form_field_name, None)
        if isinstance(data, (MultiValueDict, MergeDict)):
            return tuple([(item, related_value) for item in data.getlist(name)])

        return (
            data.get(name, None),
            related_value
        )


class RelatedModelMultipleChoiceField(RelatedModelChoiceField):
    widget = MultipleRelatedSelect
    hidden_widget = MultipleHiddenInput
    default_error_messages = {
        'list': _('Enter a list of values.'),
        'invalid_choice': _('Select a valid choice. %s is not one of the'
                            ' available choices.'),
        'invalid_pk_value': _('"%s" is not a valid value for a primary key.')
    }

    def clean(self, value):
        """
        Validates the given value and returns its "cleaned" value as an
        appropriate Python object.

        Raises ValidationError for any errors.
        """

        if self.required and not value:
            raise ValidationError(self.error_messages['required'])
        elif not self.required and not value:
            return []

        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['list'])
        key = self.to_field_name or 'pk'
        for pk, related_pk in value:
            try:
                self.queryset.filter(**{key: pk})
            except ValueError:
                raise ValidationError(self.error_messages['invalid_pk_value'] % pk)
        qs = self.queryset.filter(**{'%s__in' % key: [v[0] for v in value]})
        pks = set([(force_text(getattr(o, key)), getattr(o, '%s_id' % self.related_model_name, None)) for o in qs])
        for val, related_pk in value:
            if (force_text(val), int(related_pk)) not in pks:
                raise ValidationError(self.error_messages['invalid_choice'] % val)
        # Since this overrides the inherited ModelChoiceField.clean
        # we run custom validators here
        self.run_validators(value)
        return qs

    def prepare_value(self, value):
        if hasattr(value, '__iter__'):
            return [
                super(RelatedModelMultipleChoiceField, self).prepare_value(v)
                for v in value]
        return super(RelatedModelMultipleChoiceField, self).prepare_value(value)
