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