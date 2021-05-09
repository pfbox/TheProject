from django.forms.widgets import Select
from django_select2.forms import HeavySelect2Widget
from django.forms.widgets import Media

class utHeavyWidget(HeavySelect2Widget):
    @property
    def media(self):
        m = Media()
        #m._css_lists.append({'screen':['https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.12/css/select2.min.css']})
        m._js_lists.append([#'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.12/js/select2.min.js',
                            '/static/ut/js/django_select2.js'])
        return m

    def build_attrs(self, base_attrs, extra_attrs=None):
        #""" full copy form Select2.HeavyWidgetMixin"""
        default_attrs = {
            "data-ajax--url": self.get_url(),
            "data-ajax--cache": "true",
            "data-ajax--type": "GET",
            "data-minimum-input-length": 2,
        }

        if self.dependent_fields:
            default_attrs["data-select2-dependent-fields"] ="~" + "~".join(
                self.dependent_fields
            ) + "~"

        default_attrs.update(base_attrs)

        attrs = super().build_attrs(default_attrs, extra_attrs=extra_attrs)

        attrs["data-field_id"] = self.field_id

        attrs["class"] += " django-select2-heavy"
        return attrs

class DataAttributesSelect(Select):
    def __init__(self,attrs=None,choises=(),data={}):
        super(DataAttributesSelect,self).__init__(attrs=attrs,choices=choises)
        self.data = data

    def create_option(self,name, value, label, selected, index, subindex=None,attrs=None):
        option = super(DataAttributesSelect, self).create_option(name, value, label, selected, index, subindex=None,
                                                             attrs=None)  # noqa
        # adds the data-attributes to the attrs context var
        for data_attr, values in self.data.iteritems():
            option['attrs'][data_attr] = values[option['value']]
        return option