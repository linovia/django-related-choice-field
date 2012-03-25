
from itertools import chain
from django.forms.util import flatatt
from django.utils.safestring import mark_safe

from django import forms
from django.core.exceptions import ValidationError
from django.utils.encoding import force_unicode, smart_unicode
from django.utils.html import escape, conditional_escape
from django.utils.datastructures import MultiValueDict, MergeDict

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
            pollSelect = $('#id_poll');
            choiceSelect = $('#id_choice');

            cascadeSelect(pollSelect, choiceSelect);
        });
    </script>
"""


class LinkedSelect(forms.Select):
    allow_multiple_selected = False

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<optgroup label="%s">' %
                    escape(force_unicode(option_value)))
                for option in option_label:
                    output.append(
                        self.render_option(selected_choices, *option))
                output.append(u'</optgroup>')
            else:
                output.append(self.render_option(
                    selected_choices, option_value, option_label))

        return u'\n'.join(output)

    def render_option(self, selected_choices, option_value, option_label):
        if option_value:
            option_value, linked_option_value = option_value
            linked_option_str = u'sub_%s' % linked_option_value
        else:
            linked_option_value = None
            linked_option_str = u'static'
        option_value = force_unicode(option_value)

        option_tuple = (option_value, force_unicode(linked_option_value))
        if option_tuple in selected_choices:
            selected_html = u' selected="selected"'
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_tuple)
        else:
            selected_html = ''

        value = u'<option value="%s"%s class="%s">%s</option>' % (
            escape(option_value), selected_html, escape(linked_option_str),
            conditional_escape(force_unicode(option_label)))
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


class LinkedModelChoiceField(forms.ModelChoiceField):
    widget = LinkedSelect

    def __init__(self,
            related_form_field_name=None, related_model_name=None,
            *args, **kwargs):
        self.related_form_field_name = related_form_field_name
        self.related_model_name = related_model_name
        super(LinkedModelChoiceField, self).__init__(*args, **kwargs)
        self.widget.related_form_field_name = self.related_form_field_name

    def clean(self, value):
        """
        Validates the given value and returns its "cleaned" value as an
        appropriate Python object.

        Raises ValidationError for any errors.
        """
        value, linked_value = value
        value = super(LinkedModelChoiceField, self).clean(value)
        if int(linked_value) != \
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
        return super(LinkedModelChoiceField, self).prepare_value(value)


class MultipleLinkedSelect(LinkedSelect):
    allow_multiple_selected = True

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<select multiple="multiple"%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, value)
        if options:
            output.append(options)
        output.append('</select>')
        return mark_safe(u'\n'.join(output))

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


class LinkedModelMultipleChoiceField(LinkedModelChoiceField):
    widget = MultipleLinkedSelect

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
        for pk, linked_pk in value:
            try:
                self.queryset.filter(**{key: pk})
            except ValueError:
                raise ValidationError(self.error_messages['invalid_pk_value'] % pk)
        qs = self.queryset.filter(**{'%s__in' % key: [v[0] for v in value]})
        pks = set([force_unicode(getattr(o, key)) for o in qs])
        for val, linked_pk in value:
            if force_unicode(val) not in pks:
                raise ValidationError(self.error_messages['invalid_choice'] % val)
        # Since this overrides the inherited ModelChoiceField.clean
        # we run custom validators here
        self.run_validators(value)
        return qs

    def prepare_value(self, value):
        if hasattr(value, '__iter__'):
            return [
                super(LinkedModelMultipleChoiceField, self).prepare_value(v)
                for v in value]
        return super(LinkedModelMultipleChoiceField, self).prepare_value(value)
